#include "audio_player.hpp"

#include <cstdio>
#include <cstring>

Mp3Player::Mp3Player()
    : ready_(false), playing_(false), looping_(false), paused_(false),
      endPending_(false), handle_(nullptr), audioBuf_(nullptr),
      sampleRate_(44100), channels_(2) {
    std::memset(waveBuf_, 0, sizeof(waveBuf_));
}

Mp3Player::~Mp3Player() {
    shutdown();
}

bool Mp3Player::init() {
    if (ready_) return true;
    if (R_FAILED(ndspInit())) {
        std::printf("[audio] ndspInit failed. DSP firmware may be missing.\n");
        return false;
    }
    if (mpg123_init() != MPG123_OK) {
        ndspExit();
        std::printf("[audio] mpg123_init failed.\n");
        return false;
    }
    audioBuf_ = static_cast<u8*>(linearAlloc(NUM_BUFS * BUF_BYTES));
    if (!audioBuf_) {
        mpg123_exit();
        ndspExit();
        std::printf("[audio] linearAlloc failed.\n");
        return false;
    }
    ndspSetOutputMode(NDSP_OUTPUT_STEREO);
    ready_ = true;
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
}

bool Mp3Player::play(const std::string& path, bool loop) {
    if (!ready_ && !init()) return false;
    if (playing_ && path_ == path && looping_ == loop) return true;

    stop();

    int err = MPG123_OK;
    handle_ = mpg123_new(nullptr, &err);
    if (!handle_) {
        std::printf("[audio] mpg123_new failed: %d\n", err);
        return false;
    }

    // The game audio is stereo. Force a stable signed 16-bit output so ndsp
    // can stream it without format conversion on the CPU.
    mpg123_param(handle_, MPG123_FLAGS, MPG123_FORCE_STEREO, 0);
    mpg123_format_none(handle_);
    const long rates[] = {22050, 24000, 32000, 44100, 48000};
    for (long rate : rates) {
        mpg123_format(handle_, rate, MPG123_STEREO, MPG123_ENC_SIGNED_16);
    }

    if (mpg123_open(handle_, path.c_str()) != MPG123_OK) {
        std::printf("[audio] cannot open %s\n", path.c_str());
        mpg123_delete(handle_);
        handle_ = nullptr;
        return false;
    }

    int encoding = 0;
    if (mpg123_getformat(handle_, &sampleRate_, &channels_, &encoding) != MPG123_OK ||
        encoding != MPG123_ENC_SIGNED_16) {
        std::printf("[audio] unsupported MP3 output format: %s\n", path.c_str());
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

    std::memset(waveBuf_, 0, sizeof(waveBuf_));
    path_ = path;
    looping_ = loop;
    playing_ = true;
    paused_ = false;
    endPending_ = false;

    bool queued = false;
    for (int i = 0; i < NUM_BUFS; ++i) queued = fill(i) || queued;
    if (!queued) {
        stop();
        return false;
    }
    return true;
}

bool Mp3Player::fill(int index) {
    if (!handle_ || !audioBuf_) return false;
    u8* dst = audioBuf_ + index * BUF_BYTES;
    size_t total = 0;

    while (total < BUF_BYTES) {
        size_t done = 0;
        const int ret = mpg123_read(handle_, dst + total, BUF_BYTES - total, &done);
        total += done;
        if (ret == MPG123_DONE || ret == MPG123_ERR || done == 0) break;
    }

    if (total == 0 && looping_) {
        if (mpg123_seek(handle_, 0, SEEK_SET) >= 0) {
            size_t done = 0;
            mpg123_read(handle_, dst, BUF_BYTES, &done);
            total = done;
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

    if (endPending_ && !anyQueued) stop();
}

void Mp3Player::pause(bool value) {
    if (!ready_ || !playing_) return;
    paused_ = value;
    ndspChnSetPaused(CHANNEL, value);
}
