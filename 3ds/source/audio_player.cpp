#include "audio_player.hpp"

#include <cstdio>
#include <cstring>

namespace {

std::string shortName(const std::string& path) {
    const std::size_t slash = path.find_last_of('/');
    return slash == std::string::npos ? path : path.substr(slash + 1);
}

} // namespace

Mp3Player::Mp3Player()
    : ready_(false), playing_(false), looping_(false), paused_(false),
      endPending_(false), handle_(nullptr), audioBuf_(nullptr),
      sampleRate_(44100), channels_(2), initResult_(0),
      status_("AUDIO: NOT INITIALIZED") {
    std::memset(waveBuf_, 0, sizeof(waveBuf_));
}

Mp3Player::~Mp3Player() {
    shutdown();
}

bool Mp3Player::init() {
    if (ready_) return true;

    initResult_ = ndspInit();
    if (R_FAILED(initResult_)) {
        char buf[128];
        std::snprintf(buf, sizeof(buf), "DSP FAIL %08lX - NEED /3ds/dspfirm.cdc",
                      static_cast<unsigned long>(initResult_));
        status_ = buf;
        std::printf("[audio] %s\n", status_.c_str());
        return false;
    }

    if (mpg123_init() != MPG123_OK) {
        ndspExit();
        initResult_ = static_cast<Result>(-1);
        status_ = "MPG123 INIT FAILED";
        std::printf("[audio] %s\n", status_.c_str());
        return false;
    }

    audioBuf_ = static_cast<u8*>(linearAlloc(NUM_BUFS * BUF_BYTES));
    if (!audioBuf_) {
        mpg123_exit();
        ndspExit();
        initResult_ = static_cast<Result>(-2);
        status_ = "AUDIO BUFFER ALLOC FAILED";
        std::printf("[audio] %s\n", status_.c_str());
        return false;
    }

    ndspSetOutputMode(NDSP_OUTPUT_STEREO);
    ndspSetMasterVol(1.0f);
    ready_ = true;
    status_ = "DSP OK / MP3 READY";
    return true;
}

void Mp3Player::shutdown() {
    if (!ready_) return;
    stop();
    if (audioBuf_) {
        linearFree(audioBuf_);
        audioBuf_ = nullptr;
    }
    mpg123_exit();
    ndspExit();
    ready_ = false;
    status_ = "AUDIO SHUTDOWN";
}

void Mp3Player::stop() {
    if (!ready_) return;
    ndspChnReset(CHANNEL);
    if (handle_) {
        mpg123_close(handle_);
        mpg123_delete(handle_);
        handle_ = nullptr;
    }
    std::memset(waveBuf_, 0, sizeof(waveBuf_));
    playing_ = false;
    paused_ = false;
    endPending_ = false;
    path_.clear();
    status_ = "DSP OK / MP3 READY";
}

bool Mp3Player::play(const std::string& path, bool loop) {
    if (!ready_ && !init()) return false;
    if (playing_ && path_ == path && looping_ == loop) return true;

    stop();

    int err = MPG123_OK;
    handle_ = mpg123_new(nullptr, &err);
    if (!handle_) {
        char buf[96];
        std::snprintf(buf, sizeof(buf), "MPG123 NEW FAIL %d", err);
        status_ = buf;
        std::printf("[audio] %s\n", status_.c_str());
        return false;
    }

    // Force a stable PCM16 output. ADD_FLAGS preserves mpg123 defaults instead
    // of replacing the complete flag set.
    mpg123_param(handle_, MPG123_ADD_FLAGS, MPG123_FORCE_STEREO, 0);
    mpg123_format_none(handle_);
    const long rates[] = {22050, 24000, 32000, 44100, 48000};
    for (long rate : rates) {
        mpg123_format(handle_, rate, MPG123_STEREO, MPG123_ENC_SIGNED_16);
    }

    const int openResult = mpg123_open(handle_, path.c_str());
    if (openResult != MPG123_OK) {
        status_ = "MP3 OPEN FAIL: " + shortName(path);
        std::printf("[audio] %s (%s)\n", status_.c_str(), mpg123_strerror(handle_));
        mpg123_delete(handle_);
        handle_ = nullptr;
        return false;
    }

    int encoding = 0;
    const int formatResult = mpg123_getformat(handle_, &sampleRate_, &channels_, &encoding);
    if (formatResult != MPG123_OK || !(encoding & MPG123_ENC_SIGNED_16)) {
        status_ = "MP3 FORMAT FAIL: " + shortName(path);
        std::printf("[audio] %s rate=%ld ch=%d enc=%d\n",
                    status_.c_str(), sampleRate_, channels_, encoding);
        mpg123_close(handle_);
        mpg123_delete(handle_);
        handle_ = nullptr;
        return false;
    }

    if (channels_ != 1 && channels_ != 2) channels_ = 2;

    ndspChnReset(CHANNEL);
    ndspChnSetInterp(CHANNEL, NDSP_INTERP_LINEAR);
    ndspChnSetRate(CHANNEL, static_cast<float>(sampleRate_));
    ndspChnSetFormat(CHANNEL, channels_ == 2 ? NDSP_FORMAT_STEREO_PCM16 : NDSP_FORMAT_MONO_PCM16);
    float mix[12] = {1.0f, 1.0f, 0.0f, 0.0f, 0.0f, 0.0f,
                     0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f};
    ndspChnSetMix(CHANNEL, mix);

    std::memset(waveBuf_, 0, sizeof(waveBuf_));
    path_ = path;
    looping_ = loop;
    playing_ = true;
    paused_ = false;
    endPending_ = false;

    bool queued = false;
    for (int i = 0; i < NUM_BUFS; ++i) queued = fill(i) || queued;
    if (!queued) {
        status_ = "MP3 DECODE FAIL: " + shortName(path);
        ndspChnReset(CHANNEL);
        if (handle_) {
            mpg123_close(handle_);
            mpg123_delete(handle_);
            handle_ = nullptr;
        }
        playing_ = false;
        path_.clear();
        return false;
    }

    status_ = "PLAYING: " + shortName(path);
    return true;
}

bool Mp3Player::fill(int index) {
    if (!handle_ || !audioBuf_) return false;
    u8* dst = audioBuf_ + index * BUF_BYTES;
    size_t total = 0;

    // mpg123 may legally report NEW_FORMAT/NEED_MORE without producing bytes.
    // Keep asking until we have PCM, hit EOF/error, or the buffer is full.
    int emptyPasses = 0;
    while (total < BUF_BYTES && emptyPasses < 8) {
        size_t done = 0;
        const int ret = mpg123_read(handle_, dst + total, BUF_BYTES - total, &done);
        total += done;

        if (ret == MPG123_DONE || ret == MPG123_ERR) break;
        if (done == 0) {
            ++emptyPasses;
            if (ret != MPG123_NEW_FORMAT && ret != MPG123_NEED_MORE && ret != MPG123_OK) break;
        } else {
            emptyPasses = 0;
        }
    }

    if (total == 0 && looping_) {
        if (mpg123_seek(handle_, 0, SEEK_SET) >= 0) {
            int emptyPasses2 = 0;
            while (total < BUF_BYTES && emptyPasses2 < 8) {
                size_t done = 0;
                const int ret = mpg123_read(handle_, dst + total, BUF_BYTES - total, &done);
                total += done;
                if (ret == MPG123_DONE || ret == MPG123_ERR) break;
                if (done == 0) ++emptyPasses2;
                else emptyPasses2 = 0;
            }
        }
    }

    if (total == 0) {
        endPending_ = true;
        return false;
    }

    ndspWaveBuf& wb = waveBuf_[index];
    std::memset(&wb, 0, sizeof(wb));
    wb.data_vaddr = dst;
    wb.nsamples = total / (sizeof(s16) * channels_);
    wb.looping = false;
    DSP_FlushDataCache(dst, total);
    ndspChnWaveBufAdd(CHANNEL, &wb);
    return true;
}

void Mp3Player::update() {
    if (!ready_ || !playing_ || paused_) return;

    bool anyQueued = false;
    for (int i = 0; i < NUM_BUFS; ++i) {
        ndspWaveBuf& wb = waveBuf_[i];
        if (wb.status == NDSP_WBUF_DONE || wb.status == NDSP_WBUF_FREE) {
            if (!endPending_) fill(i);
        }
        if (wb.status == NDSP_WBUF_QUEUED || wb.status == NDSP_WBUF_PLAYING) anyQueued = true;
    }

    if (endPending_ && !anyQueued) {
        stop();
        status_ = "TRACK FINISHED";
    }
}

void Mp3Player::pause(bool value) {
    if (!ready_ || !playing_) return;
    paused_ = value;
    ndspChnSetPaused(CHANNEL, value);
    status_ = value ? "AUDIO PAUSED" : ("PLAYING: " + shortName(path_));
}
