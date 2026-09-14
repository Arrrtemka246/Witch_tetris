#pragma once
#include <3ds.h>
#include <mpg123.h>
#include <cstddef>
#include <string>

class Mp3Player {
public:
    Mp3Player();
    ~Mp3Player();

    bool init();
    void shutdown();
    bool play(const std::string& path, bool loop = true);
    void stop();
    void update();
    void pause(bool value);
    bool ready() const { return ready_; }
    bool playing() const { return playing_; }
    const std::string& path() const { return path_; }
    const std::string& status() const { return status_; }
    Result initResult() const { return initResult_; }

private:
    static const int CHANNEL = 0;
    static const int NUM_BUFS = 3;
    static const std::size_t BUF_BYTES = 32 * 1024;

    bool fill(int index);

    bool ready_;
    bool playing_;
    bool looping_;
    bool paused_;
    bool endPending_;
    mpg123_handle* handle_;
    u8* audioBuf_;
    ndspWaveBuf waveBuf_[NUM_BUFS];
    long sampleRate_;
    int channels_;
    Result initResult_;
    std::string path_;
    std::string status_;
};
