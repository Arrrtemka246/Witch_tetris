#include <3ds.h>
#include <citro2d.h>

#include "audio_player.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <deque>
#include <map>
#include <random>
#include <set>
#include <string>
#include <vector>

namespace {

constexpr int BOARD_W = 10;
constexpr int BOARD_H = 20;
constexpr float CELL = 11.9f;
constexpr float BOARD_X = 140.5f;
constexpr float BOARD_Y = 1.0f;
constexpr int LOCK_DELAY_FRAMES = 30;
constexpr int SOFT_DROP_FRAMES = 2;
constexpr int FPS = 60;

struct Point { int x; int y; };

enum PieceKind : int { I = 0, O, T, S, Z, J, L, PIECE_COUNT };
enum class FigureFallMode { Classic, Phobos };

constexpr Point BASE_SHAPES[PIECE_COUNT][4] = {
    {{0,0},{0,1},{0,2},{0,3}},
    {{0,0},{1,0},{0,1},{1,1}},
    {{0,0},{1,0},{2,0},{1,1}},
    {{0,0},{1,0},{1,1},{2,1}},
    {{1,0},{2,0},{0,1},{1,1}},
    {{0,0},{0,1},{1,1},{2,1}},
    {{2,0},{0,1},{1,1},{2,1}},
};

const char* PIECE_NAMES[PIECE_COUNT] = {"I","O","T","S","Z","J","L"};
const char* PIECE_CHARACTERS[PIECE_COUNT] = {
    "CORNELIA", "BLUNK", "CALEB", "IRMA", "WILL", "TARANEE", "HAY LIN"
};

u32 PIECE_COLORS[PIECE_COUNT];
Point SHAPES[PIECE_COUNT][4][4];

u32 color(u8 r, u8 g, u8 b, u8 a = 0xFF) {
    return C2D_Color32(r, g, b, a);
}

void initColors() {
    PIECE_COLORS[I] = color(80, 205, 235);
    PIECE_COLORS[J] = color(220, 95, 65);
    PIECE_COLORS[L] = color(165, 215, 235);
    PIECE_COLORS[O] = color(235, 190, 70);
    PIECE_COLORS[S] = color(80, 170, 235);
    PIECE_COLORS[T] = color(180, 125, 80);
    PIECE_COLORS[Z] = color(225, 90, 160);
}

void rotateLikePython(const Point src[4], Point out[4]) {
    int maxY = src[0].y;
    for (int i = 1; i < 4; ++i) maxY = std::max(maxY, src[i].y);
    const int h = maxY + 1;
    int minX = 999, minY = 999;
    for (int i = 0; i < 4; ++i) {
        out[i] = {h - 1 - src[i].y, src[i].x};
        minX = std::min(minX, out[i].x);
        minY = std::min(minY, out[i].y);
    }
    for (int i = 0; i < 4; ++i) {
        out[i].x -= minX;
        out[i].y -= minY;
    }
}

void initShapes() {
    for (int kind = 0; kind < PIECE_COUNT; ++kind) {
        for (int i = 0; i < 4; ++i) SHAPES[kind][0][i] = BASE_SHAPES[kind][i];
        for (int rot = 1; rot < 4; ++rot) rotateLikePython(SHAPES[kind][rot - 1], SHAPES[kind][rot]);
    }
}

struct Piece {
    int kind;
    int rot;
    int x;
    int y;
    Piece(int k = I, int r = 0, int px = 3, int py = 0) : kind(k), rot(r), x(px), y(py) {}
};

class Game {
public:
    Game() : rng_(static_cast<unsigned int>(osGetTime())),
             fallMode_(FigureFallMode::Classic) {
        enabled_.fill(true);
        reset();
    }

    void reset() {
        for (auto& row : board_) row.fill(-1);
        score_ = 0;
        lines_ = 0;
        gravityFrames_ = 0;
        groundedFrames_ = 0;
        holdKind_ = -1;
        holdUsed_ = false;
        gameOver_ = false;
        paused_ = false;
        history_.clear();
        classicBag_.clear();
        pieceSerial_ = 0;
        lastSeen_.fill(0);
        clearEventSerial_ = 0;
        lastCleared_ = 0;
        lastClearKind_ = -1;
        clearPending_ = false;
        clearRowCount_ = 0;
        clearFrames_ = 0;
        clearTotal_ = 0;
        clearRows_.fill(-1);
        nextKind_ = randomPiece();
        spawnPiece();
    }

    void togglePause() { if (!gameOver_) paused_ = !paused_; }
    bool paused() const { return paused_; }

    void setFallMode(FigureFallMode mode) {
        fallMode_ = mode;
        classicBag_.clear();
    }
    FigureFallMode fallMode() const { return fallMode_; }
    const char* fallModeLabel() const {
        return fallMode_ == FigureFallMode::Classic ? "CLASSIC" : "PHOBOS";
    }
    bool pieceEnabled(int kind) const {
        return kind >= 0 && kind < PIECE_COUNT ? enabled_[kind] : false;
    }
    int enabledPieceCount() const {
        int n = 0;
        for (bool v : enabled_) if (v) ++n;
        return n;
    }
    bool setPieceEnabled(int kind, bool value) {
        if (kind < 0 || kind >= PIECE_COUNT) return false;
        if (!value && enabled_[kind] && enabledPieceCount() <= 1) return false;
        enabled_[kind] = value;
        classicBag_.clear();
        return true;
    }
    bool gameOver() const { return gameOver_; }
    int score() const { return score_; }
    int lines() const { return lines_; }
    int holdKind() const { return holdKind_; }
    int nextKind() const { return nextKind_; }
    int speedFrames() const { return gravityInterval(); }
    int pieceSerial() const { return pieceSerial_; }
    int clearEventSerial() const { return clearEventSerial_; }
    int lastCleared() const { return lastCleared_; }
    int lastClearKind() const { return lastClearKind_; }
    bool clearPending() const { return clearPending_; }
    int clearRowCount() const { return clearRowCount_; }
    int clearRow(int index) const {
        return (index >= 0 && index < clearRowCount_) ? clearRows_[index] : -1;
    }
    int clearFrames() const { return clearFrames_; }
    int clearTotal() const { return clearTotal_; }
    const Piece& current() const { return current_; }
    const std::array<std::array<int, BOARD_W>, BOARD_H>& board() const { return board_; }

    void developerAddLines(int amount = 10) {
        lines_ = std::max(0, lines_ + amount);
    }

    void developerClearBoard() {
        for (auto& row : board_) row.fill(-1);
        groundedFrames_ = 0;
        gravityFrames_ = 0;
        clearPending_ = false;
        clearRowCount_ = 0;
        clearFrames_ = clearTotal_ = 0;
        clearRows_.fill(-1);
    }

    void tick(bool softDropHeld) {
        if (paused_ || gameOver_) return;
        if (clearPending_) {
            if (clearFrames_ > 0) --clearFrames_;
            if (clearFrames_ <= 0) resolvePendingClear();
            return;
        }
        const int interval = softDropHeld ? SOFT_DROP_FRAMES : gravityInterval();
        ++gravityFrames_;
        if (gravityFrames_ >= interval) {
            gravityFrames_ = 0;
            if (!move(0, 1)) {
                ++groundedFrames_;
                if (groundedFrames_ >= LOCK_DELAY_FRAMES) lockPiece();
            } else {
                groundedFrames_ = 0;
                if (softDropHeld) ++score_;
            }
        } else if (collides(current_.x, current_.y + 1, current_.rot)) {
            ++groundedFrames_;
            if (groundedFrames_ >= LOCK_DELAY_FRAMES) lockPiece();
        } else {
            groundedFrames_ = 0;
        }
    }

    bool move(int dx, int dy) {
        if (paused_ || gameOver_ || clearPending_) return false;
        const int nx = current_.x + dx;
        const int ny = current_.y + dy;
        if (!collides(nx, ny, current_.rot)) {
            current_.x = nx;
            current_.y = ny;
            if (dx != 0) groundedFrames_ = 0;
            return true;
        }
        return false;
    }

    bool rotate(int direction) {
        if (paused_ || gameOver_ || clearPending_) return false;
        const int nr = (current_.rot + direction + 4) % 4;
        constexpr int kicks[] = {0, -1, 1, -2, 2};
        for (int kick : kicks) {
            const int nx = current_.x + kick;
            if (!collides(nx, current_.y, nr)) {
                current_.x = nx;
                current_.rot = nr;
                groundedFrames_ = 0;
                return true;
            }
        }
        return false;
    }

    void hardDrop() {
        if (paused_ || gameOver_ || clearPending_) return;
        int cells = 0;
        while (move(0, 1)) ++cells;
        score_ += cells * 2;
        lockPiece();
    }

    bool hold() {
        if (paused_ || gameOver_ || clearPending_ || holdUsed_) return false;
        const int currentKind = current_.kind;
        if (holdKind_ < 0) {
            holdKind_ = currentKind;
            spawnPiece();
        } else {
            const int swap = holdKind_;
            holdKind_ = currentKind;
            current_ = Piece(swap, 0, 3, 0);
            groundedFrames_ = 0;
            gravityFrames_ = 0;
            if (collides(current_.x, current_.y, current_.rot)) gameOver_ = true;
        }
        holdUsed_ = true;
        return true;
    }

    int ghostY() const {
        int y = current_.y;
        while (!collides(current_.x, y + 1, current_.rot)) ++y;
        return y;
    }

private:
    std::array<std::array<int, BOARD_W>, BOARD_H> board_{};
    Piece current_{};
    int nextKind_ = I;
    int holdKind_ = -1;
    bool holdUsed_ = false;
    bool gameOver_ = false;
    bool paused_ = false;
    int score_ = 0;
    int lines_ = 0;
    int gravityFrames_ = 0;
    int groundedFrames_ = 0;
    int clearEventSerial_ = 0;
    int lastCleared_ = 0;
    int lastClearKind_ = -1;
    bool clearPending_ = false;
    std::array<int,4> clearRows_{{-1,-1,-1,-1}};
    int clearRowCount_ = 0;
    int clearFrames_ = 0;
    int clearTotal_ = 0;

    std::mt19937 rng_;
    FigureFallMode fallMode_;
    std::array<bool, PIECE_COUNT> enabled_{};
    std::vector<int> history_;
    std::vector<int> classicBag_;
    std::array<int, PIECE_COUNT> lastSeen_{};
    int pieceSerial_ = 0;

    int gravityInterval() const {
        const int level = lines_ / 10;
        return std::max(4, 48 - level * 4);
    }

    int randomPiece() {
        std::vector<int> candidates;
        for (int k = 0; k < PIECE_COUNT; ++k)
            if (enabled_[k]) candidates.push_back(k);
        if (candidates.empty()) return I; // setPieceEnabled() prevents this.

        if (fallMode_ == FigureFallMode::Classic) {
            bool bagValid = !classicBag_.empty();
            if (bagValid) {
                for (int k : classicBag_)
                    if (!enabled_[k]) { bagValid = false; break; }
            }
            if (!bagValid) classicBag_.clear();
            if (classicBag_.empty()) {
                classicBag_ = candidates;
                std::shuffle(classicBag_.begin(), classicBag_.end(), rng_);
            }
            const int pick = classicBag_.back();
            classicBag_.pop_back();
            return pick;
        }

        std::array<float, PIECE_COUNT> weights{};
        float total = 0.0f;
        const int recent = history_.empty() ? -1 : history_.back();
        const bool triple = history_.size() >= 3 &&
            history_[history_.size()-1] == history_[history_.size()-2] &&
            history_[history_.size()-2] == history_[history_.size()-3];

        for (int k : candidates) {
            if (triple && k == recent && candidates.size() > 1) {
                weights[k] = 0.0f;
                continue;
            }
            const int drought = std::max(0, pieceSerial_ - lastSeen_[k]);
            float w = 1.0f + std::min(drought, 14) * 0.075f;
            if (recent == k) {
                w *= 0.62f;
                if (history_.size() >= 2 && history_[history_.size()-2] == k) w *= 0.22f;
            }
            weights[k] = w;
            total += w;
        }

        if (total <= 0.0f) return candidates.front();
        std::uniform_real_distribution<float> dist(0.0f, total);
        float pick = dist(rng_);
        for (int k : candidates) {
            pick -= weights[k];
            if (pick <= 0.0f && weights[k] > 0.0f) return k;
        }
        return candidates.back();
    }

    bool collides(int x, int y, int rot) const {
        for (const Point& p : SHAPES[current_.kind][rot]) {
            const int bx = x + p.x;
            const int by = y + p.y;
            if (bx < 0 || bx >= BOARD_W || by >= BOARD_H) return true;
            if (by >= 0 && board_[by][bx] >= 0) return true;
        }
        return false;
    }

    void spawnPiece() {
        current_ = Piece(nextKind_, 0, 3, 0);
        history_.push_back(current_.kind);
        if (history_.size() > 8) history_.erase(history_.begin());
        ++pieceSerial_;
        lastSeen_[current_.kind] = pieceSerial_;
        nextKind_ = randomPiece();
        holdUsed_ = false;
        gravityFrames_ = 0;
        groundedFrames_ = 0;
        if (collides(current_.x, current_.y, current_.rot)) gameOver_ = true;
    }

    void lockPiece() {
        for (int slot = 0; slot < 4; ++slot) {
            const Point& p = SHAPES[current_.kind][current_.rot][slot];
            const int bx = current_.x + p.x;
            const int by = current_.y + p.y;
            // Encoded cell keeps kind/rotation/source-slot so the same board can
            // be re-skinned for the route selected at 200 lines.
            if (by >= 0 && by < BOARD_H && bx >= 0 && bx < BOARD_W)
                board_[by][bx] = current_.kind * 16 + current_.rot * 4 + slot;
        }

        clearRowCount_ = 0;
        clearRows_.fill(-1);
        for (int y = 0; y < BOARD_H; ++y) {
            bool full = true;
            for (int x = 0; x < BOARD_W; ++x) {
                if (board_[y][x] < 0) { full = false; break; }
            }
            if (full && clearRowCount_ < 4)
                clearRows_[clearRowCount_++] = y;
        }

        lastCleared_ = clearRowCount_;
        lastClearKind_ = current_.kind;
        ++clearEventSerial_;

        if (clearRowCount_ > 0) {
            // Desktop timing: lightning 1–3 rows = 10 frames, Tetris = 24.
            clearTotal_ = clearRowCount_ == 4 ? 24 : 10;
            clearFrames_ = clearTotal_;
            clearPending_ = true;
            gravityFrames_ = 0;
            groundedFrames_ = 0;
            return;
        }

        if (!gameOver_) spawnPiece();
    }

    void resolvePendingClear() {
        if (!clearPending_) return;

        std::array<std::array<int, BOARD_W>, BOARD_H> compact{};
        for (auto& row : compact) row.fill(-1);

        int dst = BOARD_H - 1;
        for (int y = BOARD_H - 1; y >= 0; --y) {
            bool remove = false;
            for (int i = 0; i < clearRowCount_; ++i) {
                if (clearRows_[i] == y) { remove = true; break; }
            }
            if (!remove && dst >= 0) compact[dst--] = board_[y];
        }
        board_ = compact;

        static constexpr int SCORE_TABLE[5] = {0, 100, 300, 500, 800};
        const int cleared = clearRowCount_;
        lines_ += cleared;
        score_ += SCORE_TABLE[std::min(cleared, 4)];

        clearPending_ = false;
        clearFrames_ = clearTotal_ = 0;
        clearRowCount_ = 0;
        clearRows_.fill(-1);

        if (!gameOver_) spawnPiece();
    }
};

class AssetBank {
public:
    bool has(const std::string& key) {
        return ensure(key);
    }

    C2D_Image image(const std::string& key, int index = 0) {
        C2D_Image empty{};
        if (!ensure(key)) return empty;
        auto it = sheets_.find(key);
        if (it == sheets_.end()) return empty;
        return C2D_SpriteSheetGetImage(it->second, index);
    }

    void unloadAll() {
        for (auto& kv : sheets_) C2D_SpriteSheetFree(kv.second);
        sheets_.clear();
        recent_.clear();
        failed_.clear();
    }

private:
    static constexpr std::size_t MAX_RESIDENT_SHEETS = 12;
    std::map<std::string, C2D_SpriteSheet> sheets_;
    std::vector<std::string> recent_;
    std::map<std::string, bool> failed_;

    std::string pathFor(const std::string& key) const {
        if (key == "cells") return "romfs:/gfx/phase1_cells.t3x";
        if (key == "horror_cells") return "romfs:/gfx/horror_cells.t3x";
        return std::string("romfs:/gfx/") + key + ".t3x";
    }

    void touch(const std::string& key) {
        auto it = std::find(recent_.begin(), recent_.end(), key);
        if (it != recent_.end()) recent_.erase(it);
        recent_.push_back(key);
    }

    void evictOldest() {
        if (recent_.empty()) return;
        const std::string key = recent_.front();
        recent_.erase(recent_.begin());
        auto it = sheets_.find(key);
        if (it != sheets_.end()) {
            C2D_SpriteSheetFree(it->second);
            sheets_.erase(it);
        }
    }

    bool ensure(const std::string& key) {
        auto it = sheets_.find(key);
        if (it != sheets_.end()) {
            touch(key);
            return true;
        }
        if (failed_.find(key) != failed_.end()) return false;

        while (sheets_.size() >= MAX_RESIDENT_SHEETS) evictOldest();

        const std::string path = pathFor(key);
        C2D_SpriteSheet sheet = C2D_SpriteSheetLoad(path.c_str());
        if (!sheet) {
            std::printf("[gfx] missing %s (%s)\n", key.c_str(), path.c_str());
            failed_[key] = true;
            return false;
        }

        sheets_[key] = sheet;
        touch(key);
        return true;
    }
};

C2D_TextBuf g_textBuf = nullptr;
AssetBank g_assets;

void drawText(const char* str, float x, float y, float scale, u32 col) {
    C2D_Text text;
    C2D_TextParse(&text, g_textBuf, str);
    C2D_TextOptimize(&text);
    C2D_DrawText(&text, C2D_WithColor, x, y, 0.92f, scale, scale, col);
}

void drawText(const std::string& str, float x, float y, float scale, u32 col) {
    drawText(str.c_str(), x, y, scale, col);
}

void drawImageFit(C2D_Image img, float x, float y, float w, float h, float depth = 0.1f, bool cover = false, float alpha = 1.0f) {
    if (!img.tex || !img.subtex || img.subtex->width <= 0 || img.subtex->height <= 0) return;
    const float sx = w / img.subtex->width;
    const float sy = h / img.subtex->height;
    const float s = cover ? std::max(sx, sy) : std::min(sx, sy);
    const float dw = img.subtex->width * s;
    const float dh = img.subtex->height * s;
    C2D_ImageTint tint;
    C2D_ImageTint* tintPtr = nullptr;
    if (alpha < 0.999f) {
        C2D_AlphaImageTint(&tint, alpha);
        tintPtr = &tint;
    }
    C2D_DrawImageAt(img, x + (w - dw) * 0.5f, y + (h - dh) * 0.5f, depth, tintPtr, s, s);
}

void drawAssetFit(const std::string& key, float x, float y, float w, float h, float depth = 0.1f, bool cover = false, float alpha = 1.0f) {
    if (!g_assets.has(key)) return;
    drawImageFit(g_assets.image(key), x, y, w, h, depth, cover, alpha);
}

void drawFullscreenAsset(const std::string& key, float depth = 0.05f) {
    drawAssetFit(key, 0, 0, 400, 240, depth, true);
}

void drawPanel(float x, float y, float w, float h, u32 border = 0, float depth = 0.30f) {
    C2D_DrawRectSolid(x, y, depth, w, h, color(5, 5, 12, 145));
    if (border) {
        C2D_DrawRectSolid(x, y, depth + 0.01f, w, 2, border);
        C2D_DrawRectSolid(x, y+h-2, depth + 0.01f, w, 2, border);
        C2D_DrawRectSolid(x, y, depth + 0.01f, 2, h, border);
        C2D_DrawRectSolid(x+w-2, y, depth + 0.01f, 2, h, border);
    }
}

void drawFallbackCell(float x, float y, int kind) {
    C2D_DrawRectSolid(x, y, 0.52f, CELL - 1, CELL - 1, PIECE_COLORS[kind]);
    C2D_DrawRectSolid(x + 1, y + 1, 0.53f, CELL - 3, 2, color(255,255,255,65));
}

void drawFragmentFromBank(const std::string& bank, int encoded,
                          float x, float y, float size = CELL, float depth = 0.54f) {
    const int kind = std::max(0, std::min(PIECE_COUNT - 1, encoded / 16));
    if (g_assets.has(bank)) {
        C2D_Image img = g_assets.image(bank, encoded);
        const float scale = size / 24.0f;
        C2D_DrawImageAt(img, x, y, depth, nullptr, scale, scale);
    } else {
        C2D_DrawRectSolid(x, y, depth, size - 1, size - 1, PIECE_COLORS[kind]);
    }
}

void drawFragment(int encoded, float x, float y, float size = CELL, float depth = 0.54f) {
    drawFragmentFromBank("cells", encoded, x, y, size, depth);
}

void drawPlainCell(int kind, float x, float y, float size = CELL, float depth = 0.52f) {
    kind = std::max(0, std::min(PIECE_COUNT - 1, kind));
    const u32 base = PIECE_COLORS[kind];
    C2D_DrawRectSolid(x, y, depth, size - 1, size - 1, base);
    C2D_DrawRectSolid(x + 1, y + 1, depth + 0.01f,
                      size - 3, 2, color(255,255,255,125));
    C2D_DrawRectSolid(x + 1, y + 3, depth + 0.01f,
                      2, size - 5, color(255,255,255,55));
    C2D_DrawRectSolid(x + size - 3, y + 2, depth + 0.01f,
                      2, size - 4, color(25,20,35,115));
    C2D_DrawRectSolid(x + 2, y + size - 3, depth + 0.01f,
                      size - 4, 2, color(25,20,35,105));
}

void drawRouteFragment(int encoded, float x, float y, float size, float depth,
                       bool plainPieces, bool horrorPieces) {
    const int kind = std::max(0, std::min(PIECE_COUNT - 1, encoded / 16));
    if (plainPieces) drawPlainCell(kind, x, y, size, depth);
    else if (horrorPieces)
        drawFragmentFromBank("horror_cells", encoded, x, y, size, depth);
    else
        drawFragment(encoded, x, y, size, depth);
}

void drawPieceAt(const Piece& piece, int yOverride, bool ghost = false,
                 float xShift = 0.0f, float depth = 0.52f,
                 bool plainPieces = false, bool horrorPieces = false) {
    for (int slot = 0; slot < 4; ++slot) {
        const Point& p = SHAPES[piece.kind][piece.rot][slot];
        const int gx = piece.x + p.x;
        const int gy = yOverride + p.y;
        if (gy < 0) continue;
        const float x = BOARD_X + gx * CELL + xShift;
        const float y = BOARD_Y + gy * CELL;
        if (ghost) {
            C2D_DrawRectSolid(x + 2, y + 2, depth - 0.01f,
                              CELL - 4, CELL - 4, color(210,150,255,78));
        } else {
            drawRouteFragment(piece.kind * 16 + piece.rot * 4 + slot,
                              x, y, CELL, depth, plainPieces, horrorPieces);
        }
    }
}

void drawMiniPiece(int kind, float x, float y, float cell = 8.0f) {
    for (int slot = 0; slot < 4; ++slot) {
        const Point& p = SHAPES[kind][0][slot];
        drawPlainCell(kind, x + p.x * cell, y + p.y * cell, cell, 0.82f);
    }
}

void drawCharacterMiniPiece(int kind, float x, float y, float cell = 11.0f,
                            float depth = 0.82f, bool plainPieces = false,
                            bool horrorPieces = false) {
    for (int slot = 0; slot < 4; ++slot) {
        const Point& p = SHAPES[kind][0][slot];
        const int encoded = kind * 16 + slot;
        drawRouteFragment(encoded, x + p.x * cell, y + p.y * cell,
                          cell, depth, plainPieces, horrorPieces);
    }
}

struct CodeKeyboardState {
    bool open = false;
    bool russian = false;
    bool vtdMode = false;
    int matrixFrames = 0;
    int jetixFrames = 0;
    int messageFrames = 0;
    std::string buffer;
    std::string message;
};

bool hitBox(const touchPosition& p, int x, int y, int w, int h) {
    return p.px >= x && p.px < x + w && p.py >= y && p.py < y + h;
}

void drawTouchKey(const std::string& label, float x, float y, float w, float h, bool special = false) {
    const u32 fill = special ? color(88,45,118,235) : color(28,22,39,238);
    const u32 border = special ? color(220,155,255) : color(128,95,150);
    C2D_DrawRectSolid(x, y, 0.62f, w, h, fill);
    C2D_DrawRectSolid(x, y, 0.63f, w, 1, border);
    C2D_DrawRectSolid(x, y+h-1, 0.63f, w, 1, border);
    C2D_DrawRectSolid(x, y, 0.63f, 1, h, border);
    C2D_DrawRectSolid(x+w-1, y, 0.63f, 1, h, border);
    drawText(label, x + 6, y + 7, label.size() > 4 ? 0.24f : 0.32f, color(245,240,250));
}

void renderCodeKeyboard(C3D_RenderTarget* target, const CodeKeyboardState& kb) {
    const u32 text = color(242,237,248);
    const u32 accent = color(214,145,255);
    C2D_TargetClear(target, color(10,7,17));
    C2D_SceneBegin(target);

    drawText(kb.russian ? "CODE KEYBOARD — CAPS / RU" : "CODE KEYBOARD — CAPS / EN",
             8, 7, 0.36f, accent);
    std::string shown = kb.buffer.empty() ? "_" : kb.buffer;
    if (shown.size() > 24) shown = shown.substr(shown.size()-24);
    drawText("CODE: " + shown, 8, 29, 0.30f, text);

    if (!kb.russian) {
        const char* rows[] = {"QWERTYUIOP","ASDFGHJKL","ZXCVBNM"};
        const int starts[] = {5,20,45};
        const int widths[] = {30,31,32};
        const int ys[] = {55,92,129};
        for (int r=0;r<3;++r) {
            for (int i=0; rows[r][i]; ++i) {
                std::string label(1, rows[r][i]);
                drawTouchKey(label, starts[r] + i*widths[r], ys[r], widths[r]-2, 29, label=="Q");
            }
        }
    } else {
        static const char* row1[]={"Й","Ц","У","К","Е","Н","Г","Ш","Щ","З","Х"};
        static const char* row2[]={"Ф","Ы","В","А","П","Р","О","Л","Д","Ж","Э"};
        static const char* row3[]={"Я","Ч","С","М","И","Т","Ь","Б","Ю","Ё"};
        const char** rows[]={row1,row2,row3};
        const int counts[]={11,11,10};
        const int starts[]={2,2,16};
        const int widths[]={28,28,29};
        const int ys[]={55,92,129};
        for(int r=0;r<3;++r)
            for(int i=0;i<counts[r];++i)
                drawTouchKey(rows[r][i], starts[r]+i*widths[r], ys[r], widths[r]-2, 29);
    }

    drawTouchKey("CLEAR", 7, 173, 67, 31, true);
    drawTouchKey(kb.russian ? "EN" : "RU", 80, 173, 52, 31, true);
    drawTouchKey("CLOSE", 138, 173, 72, 31, true);
    drawTouchKey("ENTER", 216, 173, 96, 31, true);

    if (!kb.russian)
        drawText("Q = SHIFT+Q DEV CHEAT (+10 LINES)", 8, 211, 0.27f, color(245,180,205));
    else
        drawText("Codes trigger as soon as the word is complete.", 8, 211, 0.25f, text);

    if (kb.messageFrames > 0 && !kb.message.empty())
        drawText(kb.message, 8, 228, 0.25f, accent);
}

std::string codeTouchToken(const touchPosition& p, bool russian) {
    if (hitBox(p,7,173,67,31)) return "<CLEAR>";
    if (hitBox(p,80,173,52,31)) return "<LANG>";
    if (hitBox(p,138,173,72,31)) return "<CLOSE>";
    if (hitBox(p,216,173,96,31)) return "<ENTER>";

    if (!russian) {
        const char* rows[] = {"QWERTYUIOP","ASDFGHJKL","ZXCVBNM"};
        const int starts[] = {5,20,45};
        const int widths[] = {30,31,32};
        const int ys[] = {55,92,129};
        for (int r=0;r<3;++r) {
            for (int i=0; rows[r][i]; ++i) {
                if (hitBox(p, starts[r]+i*widths[r], ys[r], widths[r]-2, 29))
                    return std::string(1, rows[r][i]);
            }
        }
    } else {
        static const char* row1[]={"Й","Ц","У","К","Е","Н","Г","Ш","Щ","З","Х"};
        static const char* row2[]={"Ф","Ы","В","А","П","Р","О","Л","Д","Ж","Э"};
        static const char* row3[]={"Я","Ч","С","М","И","Т","Ь","Б","Ю","Ё"};
        const char** rows[]={row1,row2,row3};
        const int counts[]={11,11,10};
        const int starts[]={2,2,16};
        const int widths[]={28,28,29};
        const int ys[]={55,92,129};
        for(int r=0;r<3;++r)
            for(int i=0;i<counts[r];++i)
                if(hitBox(p,starts[r]+i*widths[r],ys[r],widths[r]-2,29))
                    return rows[r][i];
    }
    return "";
}


std::string phaseBackground(int lines, bool phobosRoute = false) {
    if (lines >= 200) return phobosRoute ? "bg_phase1" : "bg_phase2";
    if (lines >= 100) return "bg_phase1";
    return "bg_phase0";
}

void renderTetrisTop(const Game& game, C3D_RenderTarget* target,
                    const CodeKeyboardState& codes,
                    bool guardiansRoute, bool phobosRoute,
                    float eyeShift = 0.0f) {
    const bool matrixMode = codes.matrixFrames > 0 || codes.vtdMode;
    const u32 text = color(245, 240, 250);
    const u32 accent = matrixMode ? color(90,255,120) : color(209, 143, 255);
    const u32 grid = matrixMode ? color(30,145,65,145) : color(130, 105, 150, 112);

    const float bgShift     =  eyeShift * 1.35f;
    const float pieceShift  =  eyeShift * 0.30f;
    const float glassShift  = -eyeShift * 0.50f;
    const float hudShift    = -eyeShift * 0.90f;
    const float phobosShift = -eyeShift * 3.85f;

    C2D_TargetClear(target, color(9, 7, 15));
    C2D_SceneBegin(target);

    // The Tetris well is now the visual centre of the 400x240 display.
    drawAssetFit(phaseBackground(game.lines(), phobosRoute), -7 + bgShift, -4, 414, 248,
                 0.08f, true, 1.0f);
    C2D_DrawRectSolid(0, 0, 0.18f, 400, 240, color(0,0,0,22));
    if (matrixMode) {
        C2D_DrawRectSolid(0,0,0.19f,400,240,color(0,48,15,138));
        for(int i=0;i<20;++i) {
            const float x=static_cast<float>((i*47 + codes.matrixFrames*2)%400);
            const float y=static_cast<float>((i*83 + codes.matrixFrames)%240);
            C2D_DrawRectSolid(x,y,0.20f,2,9,color(35,185,72,65));
        }
    }

    C2D_DrawRectSolid(BOARD_X - 2, BOARD_Y - 1, 0.34f,
                      BOARD_W * CELL + 4, BOARD_H * CELL + 2,
                      color(7,7,14,192));

    // Pieces live behind the glass plane.
    const auto& board = game.board();
    for (int y = 0; y < BOARD_H; ++y) {
        for (int x = 0; x < BOARD_W; ++x) {
            if (board[y][x] >= 0)
                drawFragment(board[y][x],
                             BOARD_X + x * CELL + pieceShift,
                             BOARD_Y + y * CELL,
                             CELL, 0.50f);
        }
    }

    if (!game.gameOver()) {
        drawPieceAt(game.current(), game.ghostY(), true, pieceShift, 0.49f);
        drawPieceAt(game.current(), game.current().y, false, pieceShift, 0.52f);
    }

    // Glass/grid plane, intentionally in front of the blocks.
    const float glassX = BOARD_X + glassShift;
    for (int x = 1; x < BOARD_W; ++x)
        C2D_DrawRectSolid(glassX + x * CELL, BOARD_Y, 0.60f,
                          1, BOARD_H * CELL, grid);
    for (int y = 1; y < BOARD_H; ++y)
        C2D_DrawRectSolid(glassX, BOARD_Y + y * CELL, 0.60f,
                          BOARD_W * CELL, 1, grid);

    const u32 glassEdge = color(191, 128, 225, 220);
    const u32 glassShine = color(245, 222, 255, 105);
    C2D_DrawRectSolid(glassX - 2, BOARD_Y, 0.62f,
                      BOARD_W * CELL + 4, 2, glassEdge);
    C2D_DrawRectSolid(glassX - 2, BOARD_Y + BOARD_H * CELL - 2, 0.62f,
                      BOARD_W * CELL + 4, 2, glassEdge);
    C2D_DrawRectSolid(glassX - 2, BOARD_Y, 0.62f,
                      2, BOARD_H * CELL, glassEdge);
    C2D_DrawRectSolid(glassX + BOARD_W * CELL, BOARD_Y, 0.62f,
                      2, BOARD_H * CELL, glassEdge);
    C2D_DrawRectSolid(glassX, BOARD_Y, 0.63f,
                      2, BOARD_H * CELL, glassShine);

    // Compact floating HUD — no more three full-height framed columns.
    C2D_DrawRectSolid(7 + hudShift, 7, 0.65f, 116, 111, color(5,5,12,112));
    C2D_DrawRectSolid(277 + hudShift, 7, 0.65f, 116, 105, color(5,5,12,112));
    C2D_DrawRectSolid(277 + hudShift, 119, 0.65f, 116, 106, color(5,5,12,105));

    char buf[96];
    drawText("W.I.T.C.H. TETRIS", 14 + hudShift, 13, 0.38f, accent);
    std::snprintf(buf, sizeof(buf), "LINES %d", game.lines());
    drawText(buf, 14 + hudShift, 43, 0.34f, text);
    std::snprintf(buf, sizeof(buf), "SCORE %d", game.score());
    drawText(buf, 14 + hudShift, 62, 0.34f, text);
    std::snprintf(buf, sizeof(buf), "SPEED %df", game.speedFrames());
    drawText(buf, 14 + hudShift, 81, 0.34f, text);

    const char* phase = codes.vtdMode ? "VTD / VALENTIN" :
                        (game.lines() >= 200 ? (phobosRoute ? "PHOBOS WINS" : "GUARDIANS") :
                         (game.lines() >= 100 ? "RESISTANCE" : "PHOBOS"));
    drawText(phase, 14 + hudShift, 101, 0.28f, accent);

    drawText("NEXT", 285 + hudShift, 14, 0.34f, accent);
    drawCharacterMiniPiece(game.nextKind(), 315 + hudShift, 38, 12.0f, 0.83f);
    drawText(PIECE_CHARACTERS[game.nextKind()], 284 + hudShift, 88, 0.24f, text);

    drawText("HOLD", 285 + hudShift, 126, 0.34f, accent);
    if (game.holdKind() >= 0) {
        drawCharacterMiniPiece(game.holdKind(), 315 + hudShift, 151, 11.0f, 0.83f);
        drawText(PIECE_CHARACTERS[game.holdKind()], 284 + hudShift, 199, 0.24f, text);
    }
    drawText("START/SELECT PAUSE", 281 + hudShift, 214, 0.20f, text);

    // Phobos / Valentin observer occupies the closest character plane.
    const float phobosX = 17 + phobosShift;
    if (codes.vtdMode) {
        C2D_DrawCircleSolid(phobosX + 52,177,0.71f,43,color(40,210,80,24));
        drawAssetFit("vtd_observer",phobosX,116,110,116,0.79f,false,1.0f);
        drawText("VALENTIN",phobosX+27,214,0.25f,color(105,255,135));
    } else if (!(guardiansRoute && game.lines()>=200)) {
        const std::string phobosKey =
            (phobosRoute && game.lines()>=200) ? "intro_phobos_cast" :
            (game.lines() >= 100 ? "phobos_resistance" : "phobos_gameplay");
        C2D_DrawCircleSolid(phobosX + 52, 177, 0.71f, 42, color(170,90,215,18));
        drawAssetFit(phobosKey, phobosX, 121, 108, 111, 0.78f, false, 1.0f);
    }

    if (codes.matrixFrames > 0 && !codes.vtdMode)
        drawText("MATRIX", 294, 219, 0.32f, color(90,255,120));

    if (codes.jetixFrames > 0) {
        // Desktop v6.5-inspired cameo: deterministic confetti + bouncing logo.
        const int elapsed=FPS*6-codes.jetixFrames;
        const u32 palette[]={
            color(255,70,70),color(255,190,40),color(80,220,120),
            color(80,180,255),color(210,90,255),color(255,110,190)
        };
        for(int i=0;i<34;++i) {
            const float x=static_cast<float>((i*89 + elapsed*(4+i%3))%400);
            const float y=static_cast<float>((i*137 + elapsed*(3+i%4))%240);
            if(i%3==0) C2D_DrawRectSolid(x,y,0.90f,4,7,palette[i%6]);
            else C2D_DrawCircleSolid(x,y,0.90f,2+(i%3),palette[i%6]);
        }
        const float t=std::max(0.0f,std::min(1.0f,elapsed/(FPS*6.0f)));
        float y=64.0f;
        float x=326.0f;
        if(t<0.28f) {
            const float local=t/0.28f;
            y-=38.0f*std::abs(std::sin(local*3.1415926f*2.2f))*(1.0f-local*0.5f);
        } else if(t<0.72f) {
            const float local=(t-0.28f)/0.44f;
            y-=8.0f*std::sin(local*3.1415926f*2.0f);
        } else {
            const float local=(t-0.72f)/0.28f;
            y-=150.0f*local;
            x+=72.0f*local;
        }
        const float wink=(t>0.18f&&t<0.23f)?0.82f:1.0f;
        drawAssetFit("jetix_logo",x-48.0f*wink,y-36,96.0f*wink,72,0.94f,false,1.0f);
    }

    if (game.paused()) {
        const float pauseShift = -eyeShift * 5.20f;
        C2D_DrawRectSolid(0,0,0.91f,400,240,color(0,0,0,54));
        drawPanel(92 + pauseShift, 78, 216, 82, accent, 0.95f);
        drawText("PAUSED", 146 + pauseShift, 96, 0.66f, accent);
        drawText("START / SELECT: RESUME", 109 + pauseShift, 128, 0.33f, text);
    } else if (game.gameOver()) {
        drawPanel(78, 72, 244, 98, color(225,75,95), 0.90f);
        drawText("GAME OVER", 120, 92, 0.66f, color(245,100,115));
        drawText("A: restart", 145, 126, 0.42f, text);
        drawText("B: menu", 151, 147, 0.36f, text);
    }
}

void renderTetrisBottom(const Game& game, C3D_RenderTarget* target,
                        const Mp3Player& audio, const CodeKeyboardState& codes,
                        bool guardiansRoute, bool phobosRoute) {
    if (codes.open) {
        renderCodeKeyboard(target, codes);
        return;
    }

    const u32 text = color(238, 234, 246);
    const u32 accent = color(205, 140, 255);

    C2D_TargetClear(target, color(12, 9, 20));
    C2D_SceneBegin(target);

    drawAssetFit(phaseBackground(game.lines(), phobosRoute), 0, 0, 320, 240, 0.05f, true, 1.0f);
    C2D_DrawRectSolid(0, 0, 0.20f, 320, 240, color(0,0,0,62));

    drawPanel(7, 7, 172, 226, accent, 0.28f);
    drawText("CONTROLS", 16, 15, 0.39f, accent);
    drawText("LEFT / RIGHT  MOVE", 16, 40, 0.27f, text);
    drawText("DOWN   SOFT DROP", 16, 56, 0.27f, text);
    drawText("UP / A / B  ROTATE", 16, 72, 0.27f, text);
    drawText("Y      HARD DROP", 16, 88, 0.27f, text);
    drawText("X      HOLD", 16, 104, 0.27f, text);
    drawText("L / R  PREV / NEXT MUSIC", 16, 120, 0.24f, text);
    drawText("START / SELECT  PAUSE", 16, 136, 0.25f, text);

    drawText("AUDIO", 16, 158, 0.29f, accent);
    std::string status = audio.status();
    const bool audioError = status.find("FAIL") != std::string::npos;
    const u32 audioColor = audioError ? color(245,105,115) : text;
    drawText(status.substr(0, 23), 16, 176, 0.23f, audioColor);
    if (status.size() > 23)
        drawText(status.substr(23, 23), 16, 191, 0.23f, audioColor);

    C2D_DrawRectSolid(13, 208, 0.70f, 152, 22, color(92,47,123,235));
    drawText("TOUCH: CODE KEYBOARD", 23, 214, 0.27f, color(250,240,255));

    if(codes.vtdMode) {
        C2D_DrawRectSolid(174,4,0.50f,142,226,color(0,55,18,95));
        drawAssetFit("vtd_observer",174,4,142,226,0.58f,false,1.0f);
        drawText("VALENTIN",236,211,0.27f,color(105,255,135));
        drawText("L+R: EXIT VTD -> CLASSIC",181,222,0.20f,color(105,255,135));
    } else if(!(guardiansRoute && game.lines()>=200)) {
        const std::string phobosKey =
            (phobosRoute && game.lines()>=200) ? "intro_phobos_cast" :
            (game.lines() >= 100 ? "phobos_resistance" : "phobos_gameplay");
        drawAssetFit(phobosKey, 174, 4, 142, 226, 0.58f, false, 1.0f);
        drawText("PHOBOS", 244, 211, 0.29f, accent);
    } else {
        drawText("GUARDIANS ROUTE",196,112,0.34f,accent);
    }

    if (codes.messageFrames > 0 && !codes.message.empty()) {
        drawPanel(179, 8, 136, 37, accent, 0.84f);
        drawText(codes.message.substr(0, 22), 187, 20, 0.24f, text);
    }
}

enum class Mode {
    Intro,
    Menu,
    Settings,
    Tetris,
    CutsceneMenu,
    Cutscene,
    RouteChoice,
    MiniMenu,
    MiniGame,
    PhobosRoom
};

enum class CutsceneKind {
    Intro,
    Lines100,
    Lines200,
    Ending
};

const char* INTRO_ASSET_KEYS[PIECE_COUNT] = {
    "cornelia", "blunk", "caleb", "irma", "will", "taranee", "haylin"
};

struct IntroState {
    int scene;
    int frames;
    int transformKind;
    int secondKind;
    bool transformAll;
    bool horrorIrma;

    IntroState()
        : scene(0), frames(0), transformKind(I), secondKind(T),
          transformAll(false), horrorIrma(false) {}
};

void rerollIntro(IntroState& intro, std::mt19937& rng) {
    intro.scene = 0;
    intro.frames = 0;
    std::uniform_int_distribution<int> kindDist(0, PIECE_COUNT - 1);
    std::uniform_int_distribution<int> coin(0, 1);
    std::uniform_int_distribution<int> horror(0, 9);

    intro.transformAll = coin(rng) == 0;
    intro.transformKind = kindDist(rng);
    // Avoid making Will the second close-up every time he already opened.
    do { intro.secondKind = kindDist(rng); } while (intro.secondKind == Z);
    intro.horrorIrma = horror(rng) == 0;
}

std::string introAssetKey(int kind, const char* stage) {
    return std::string("intro_") + INTRO_ASSET_KEYS[kind] + "_" + stage;
}

struct CutsceneState {
    CutsceneKind kind;
    int frame;
    Mode returnMode;
    u64 startedMs;

    CutsceneState()
        : kind(CutsceneKind::Lines100), frame(0),
          returnMode(Mode::CutsceneMenu), startedMs(0) {}
};

const char* MENU_ITEMS[] = {
    "NEW GAME",
    "SETTINGS",
    "CUTSCENES",
    "PHOBOS ROOM",
    "EXIT"
};
constexpr int MENU_COUNT = sizeof(MENU_ITEMS) / sizeof(MENU_ITEMS[0]);

const char* CUTSCENE_ITEMS[] = {
    "INTRO — PHOBOS CURSE",
    "100 LINES — RESISTANCE",
    "200 LINES — COLLAPSE",
    "ENDING — W.I.T.C.H."
};
constexpr int CUTSCENE_COUNT = sizeof(CUTSCENE_ITEMS) / sizeof(CUTSCENE_ITEMS[0]);

void renderMenu(C3D_RenderTarget* top, C3D_RenderTarget* bottom,
                int selected, const Mp3Player& audio, float eyeShift = 0.0f) {
    const u32 accent = color(211,143,255);
    const u32 text = color(245,240,250);

    // Menu stereo stack:
    // far palace -> menu plane -> selected-row glow -> Phobos foreground.
    const float bgShift        =  eyeShift * 1.40f;
    const float menuShift      = -eyeShift * 0.25f;
    const float selectedShift  = -eyeShift * 1.30f;
    const float phobosShift    = -eyeShift * 4.40f;

    C2D_TargetClear(top, color(8,7,14));
    C2D_SceneBegin(top);

    // Far layer. Overscan keeps the edges filled when the 3D slider is high.
    drawAssetFit("bg_menu", -7 + bgShift, -4, 414, 248, 0.08f, true, 1.0f);
    C2D_DrawRectSolid(0, 0, 0.18f, 400, 240, color(0,0,0,56));

    // Middle layer — menu card.
    drawPanel(13 + menuShift, 12, 220, 215, accent, 0.50f);
    drawText("W.I.T.C.H.", 28 + menuShift, 26, 0.72f, accent);
    drawText("TETRIS", 28 + menuShift, 52, 0.62f, text);
    drawText("NINTENDO 3DS", 28 + menuShift, 75, 0.34f, accent);

    for (int i = 0; i < MENU_COUNT; ++i) {
        const float y = 105 + i * 22;
        const bool active = i == selected;
        const float rowShift = active ? selectedShift : menuShift;

        if (active) {
            // Selected item sits one plane closer than the menu card. Three
            // translucent rectangles act as the "lit / protruding" edge the
            // physical 3DS display is good at emphasizing.
            C2D_DrawRectSolid(20 + selectedShift, y - 6, 0.68f,
                              199, 25, color(173,92,218,35));
            C2D_DrawRectSolid(22 + selectedShift, y - 5, 0.70f,
                              195, 23, color(191,105,235,58));
            C2D_DrawRectSolid(24 + selectedShift, y - 3, 0.72f,
                              190, 19, color(111,56,143,235));
            C2D_DrawRectSolid(24 + selectedShift, y - 3, 0.73f,
                              190, 1, color(241,205,255,180));
            C2D_DrawRectSolid(24 + selectedShift, y + 15, 0.73f,
                              190, 1, color(160,95,205,150));
        }

        drawText(std::string(active ? "> " : "  ") + MENU_ITEMS[i],
                 29 + rowShift, y, 0.40f,
                 active ? color(255,247,255) : text);
    }

    // Foreground layer — Phobos. A very soft purple aura is kept behind the
    // sprite to strengthen the pop-out without looking like a solid card.
    const float px = 228 + phobosShift;
    C2D_DrawCircleSolid(px + 82, 104, 0.58f, 62, color(157,72,210,18));
    C2D_DrawCircleSolid(px + 82, 126, 0.59f, 48, color(213,145,255,16));
    if (g_assets.has("phobos_menu_body"))
        drawAssetFit("phobos_menu_body", px, 20, 165, 212, 0.76f, false, 0.98f);
    drawText("PHOBOS", px + 69, 211, 0.27f, color(231,184,255));

    C2D_TargetClear(bottom, color(13,10,22));
    C2D_SceneBegin(bottom);
    drawText("W.I.T.C.H. TETRIS 3DS", 12, 14, 0.52f, accent);
    drawText("Tetris + story + Phobos Room", 12, 53, 0.38f, text);
    drawText("Mini-games are hidden until redesign.", 12, 78, 0.34f, text);

    drawText("AUDIO STATUS", 12, 112, 0.34f, accent);
    std::string audioStatus = audio.status();
    const bool audioError = audioStatus.find("FAIL") != std::string::npos;
    const u32 audioColor = audioError ? color(245,105,115) : text;
    drawText(audioStatus.substr(0, 34), 12, 134, 0.29f, audioColor);
    if (audioStatus.size() > 34)
        drawText(audioStatus.substr(34, 34), 12, 151, 0.29f, audioColor);
    if (audioError)
        drawText("Send me this red line if there is no sound.", 12, 177, 0.29f,
                 color(245,170,180));

    drawText("D-Pad: select    A: open    START: exit", 12, 207, 0.36f, accent);
}

void renderSettings(C3D_RenderTarget* top, C3D_RenderTarget* bottom,
                    const Game& game, int page, int selected,
                    float eyeShift = 0.0f) {
    const u32 accent = color(211,143,255);
    const u32 text = color(245,240,250);
    const float bgShift = eyeShift * 1.35f;
    const float panelShift = -eyeShift * 0.35f;
    const float choiceShift = -eyeShift * 1.20f;

    C2D_TargetClear(top, color(8,7,14));
    C2D_SceneBegin(top);
    drawAssetFit("bg_menu", -7 + bgShift, -4, 414, 248, 0.08f, true, 1.0f);
    C2D_DrawRectSolid(0,0,0.18f,400,240,color(0,0,0,70));
    drawPanel(37 + panelShift, 13, 326, 214, accent, 0.50f);

    if (page == 0) {
        drawText("SETTINGS", 132 + panelShift, 26, 0.60f, accent);
        const char* items[]={"FIGURE FALL MODE","CHARACTERS","BACK"};
        for(int i=0;i<3;++i) {
            const float y=83+i*45;
            if(i==selected)
                C2D_DrawRectSolid(61+choiceShift,y-6,0.72f,278,32,color(102,52,132,225));
            drawText(std::string(i==selected?"> ":"  ")+items[i],
                     76+(i==selected?choiceShift:panelShift),y,0.38f,
                     i==selected?accent:text);
        }
        drawText(std::string("MODE: ")+game.fallModeLabel(),
                 103+panelShift,55,0.34f,text);
    } else {
        drawText("SETTINGS — CHARACTERS", 69 + panelShift, 24, 0.47f, accent);
        drawText("A toggles a tetromino / character", 82 + panelShift, 49, 0.27f, text);
        const char* labels[PIECE_COUNT]={"CORNELIA / I","BLUNK / O","CALEB / T",
                                        "IRMA / S","WILL / Z","TARANEE / J","HAY LIN / L"};
        for(int i=0;i<PIECE_COUNT;++i) {
            const float y=73+i*21;
            if(i==selected)
                C2D_DrawRectSolid(57+choiceShift,y-3,0.72f,286,20,color(102,52,132,225));
            const std::string state=game.pieceEnabled(i)?"ACTIVE":"DELETED";
            drawText(std::string(i==selected?"> ":"  ")+labels[i],
                     68+(i==selected?choiceShift:panelShift),y,0.28f,
                     i==selected?accent:text);
            drawText(state, 281+(i==selected?choiceShift:panelShift),y,0.23f,
                     game.pieceEnabled(i)?color(130,240,160):color(245,95,110));
        }
        const int back=PIECE_COUNT;
        const float by=220;
        if(selected==back)
            C2D_DrawRectSolid(132+choiceShift,by-4,136,19,0.72f,color(102,52,132,225));
        drawText(std::string(selected==back?"> ":"  ")+"BACK",
                 160+(selected==back?choiceShift:panelShift),by,0.28f,
                 selected==back?accent:text);
    }

    C2D_TargetClear(bottom, color(12,9,20));
    C2D_SceneBegin(bottom);
    if(page==0) {
        drawText("GAME SETTINGS",12,18,0.46f,accent);
        drawText("Classic: independent seven-piece bag.",12,61,0.35f,text);
        drawText("Phobos: controlled chaos and repeats.",12,88,0.34f,text);
        drawText("A / LEFT / RIGHT changes the selected item.",12,131,0.31f,text);
    } else {
        drawText("CHARACTER ROSTER",12,18,0.46f,accent);
        drawText("Deleted pieces stop spawning and disappear",12,62,0.33f,text);
        drawText("from NEXT and their gameplay reactions.",12,87,0.33f,text);
        drawText("At least one piece must remain active.",12,122,0.33f,accent);
    }
    drawText("B / START — BACK",12,207,0.39f,accent);
}

void renderRouteChoice(C3D_RenderTarget* top, C3D_RenderTarget* bottom,
                       int selected, float eyeShift = 0.0f) {
    const u32 accent=color(211,143,255), text=color(245,240,250);
    const float bgShift=eyeShift*1.2f, actorShift=-eyeShift*2.2f, uiShift=-eyeShift*0.9f;

    C2D_TargetClear(top,color(5,3,9));
    C2D_SceneBegin(top);
    drawAssetFit("bg_phase1",-6+bgShift,-3,412,246,0.08f,true,1.0f);
    C2D_DrawRectSolid(0,0,0.22f,400,240,color(0,0,0,86));
    drawAssetFit("l100_will",20+actorShift,46,118,165,0.52f);
    drawAssetFit("intro_phobos_cast",265-actorShift,31,120,180,0.56f);
    drawPanel(82+uiShift,12,236,49,accent,0.76f);
    drawText("WHO WINS?",132+uiShift,27,0.54f,text);

    const float gx=33, px=211, y=160, w=156, h=48;
    if(selected==0) C2D_DrawRectSolid(gx+uiShift,y,0.83f,w,h,color(70,105,155,235));
    else C2D_DrawRectSolid(px+uiShift,y,0.83f,w,h,color(105,45,130,235));
    drawText(std::string(selected==0?"> ":"  ")+"GUARDIANS",
             gx+17+uiShift,y+16,0.38f,selected==0?color(180,225,255):text);
    drawText(std::string(selected==1?"> ":"  ")+"PHOBOS",
             px+31+uiShift,y+16,0.38f,selected==1?accent:text);

    C2D_TargetClear(bottom,color(10,7,17));
    C2D_SceneBegin(bottom);
    drawText("200 LINES — CHOOSE THE WINNER",12,18,0.43f,accent);
    drawText("LEFT / RIGHT — choose",12,72,0.39f,text);
    drawText("A / TOUCH — confirm",12,103,0.39f,text);
    drawText("This choice changes the post-200 route,",12,150,0.32f,text);
    drawText("music and Phobos Room behaviour.",12,175,0.32f,text);
}

void renderIntro(C3D_RenderTarget* top, C3D_RenderTarget* bottom,
                 const IntroState& intro, float eyeShift = 0.0f) {
    const u32 accent = color(215,145,255);
    const u32 text = color(245,240,250);
    const int scene = intro.scene;

    // Cutscene stereo stack: scenery behind the screen, characters forward,
    // dialogue/UI close to the screen plane. This is deliberately gentler
    // than gameplay Phobos so rapid scene changes stay comfortable.
    const float bgShift = eyeShift * 1.15f;
    const float actorShift = -eyeShift * 2.05f;
    const float frontShift = -eyeShift * 3.05f;
    const float uiShift = -eyeShift * 0.65f;

    C2D_TargetClear(top, color(3,3,8));
    C2D_SceneBegin(top);

    if (scene == 0) {
        drawAssetFit("intro_castle", -6 + bgShift, -3, 412, 246, 0.08f, true, 1.0f);
        C2D_DrawRectSolid(0, 0, 0.30f, 400, 240, color(0,0,0,42));
        drawPanel(36 + uiShift, 162, 328, 58, accent, 0.80f);
        drawText("MERIDIAN — PHOBOS CASTLE", 72 + uiShift, 178, 0.42f, text);
    } else {
        drawAssetFit("intro_throne", -6 + bgShift, -3, 412, 246, 0.08f, true, 1.0f);
        C2D_DrawRectSolid(0, 0, 0.25f, 400, 240, color(0,0,0,28));

        if (scene == 1) {
            drawAssetFit("intro_will", 30 + actorShift, 48, 135, 172, 0.46f);
            drawAssetFit("intro_phobos", 248 + frontShift, 24, 145, 200, 0.55f);
            drawPanel(48 + uiShift, 176, 304, 48, accent, 0.80f);
            drawText("WILL: IT'S OVER, PHOBOS!", 75 + uiShift, 191, 0.41f, text);
        } else if (scene == 2) {
            const std::string key = std::string("intro_") + INTRO_ASSET_KEYS[intro.secondKind];
            drawAssetFit(key, 120 + actorShift, 24, 160, 197, 0.52f);
            drawPanel(48 + uiShift, 176, 304, 48, accent, 0.80f);
            drawText(std::string(PIECE_CHARACTERS[intro.secondKind]) + ": WE WON'T SURRENDER!",
                     63 + uiShift, 191, 0.34f, text);
        } else if (scene == 3) {
            const bool casting = intro.frames > 95;
            drawAssetFit(casting ? "intro_phobos_cast" : "intro_phobos",
                         100 + frontShift, 16, 200, 207, 0.57f);
            drawPanel(42 + uiShift, 176, 316, 48, accent, 0.80f);
            drawText("PHOBOS: EVERYTHING IS JUST BEGINNING.",
                     55 + uiShift, 191, 0.33f, text);
        } else if (scene == 4) {
            drawAssetFit("intro_phobos_cast", 90 + frontShift, 10, 220, 216, 0.61f);
            const int pulse = (intro.frames / 8) % 2;
            if (pulse)
                C2D_DrawRectSolid(0,0,0.73f,400,240,color(220,175,255,52));
            drawText("THE SPELL", 150 + uiShift, 202, 0.40f, accent);
        } else if (scene == 5) {
            C2D_DrawRectSolid(0,0,0.35f,400,240,color(35,0,55,80));
            const int stage = intro.frames < 32 ? 0 :
                              intro.frames < 78 ? 1 :
                              intro.frames < 132 ? 2 : 3;
            const char* stageName = stage == 0 ? "normal" :
                                    stage == 1 ? "t1" :
                                    stage == 2 ? "t2" : "final";

            if (intro.transformAll) {
                const float xs[PIECE_COUNT] = {23, 74, 125, 176, 227, 278, 329};
                for (int kind=0; kind<PIECE_COUNT; ++kind) {
                    std::string key = introAssetKey(kind, stageName);
                    drawAssetFit(key, xs[kind] + actorShift, 64 + (kind%2)*10,
                                 52, 142, 0.58f);
                }
                drawPanel(43 + uiShift, 187, 314, 38, accent, 0.81f);
                drawText("ALL SEVEN ARE TRANSFORMING", 78 + uiShift, 198, 0.34f, text);
            } else {
                std::string key;
                if (intro.transformKind == S && intro.horrorIrma && stage == 2)
                    key = "intro_irma_horror";
                else
                    key = introAssetKey(intro.transformKind, stageName);

                drawAssetFit(key, 115 + actorShift, 16, 170, 205, 0.59f);
                drawPanel(48 + uiShift, 177, 304, 47, accent, 0.82f);
                drawText(std::string(PIECE_CHARACTERS[intro.transformKind]) + " — TRANSFORMATION",
                         78 + uiShift, 191, 0.35f, text);
            }
        } else if (scene == 6) {
            drawAssetFit("intro_phobos", 104 + frontShift, 14, 192, 210, 0.58f);
            drawPanel(48 + uiShift, 177, 304, 47, accent, 0.82f);
            drawText("PHOBOS: NOW YOUR POWER IS MINE.",
                     67 + uiShift, 191, 0.34f, text);
        } else {
            drawAssetFit("bg_phase0", -6 + bgShift, -3, 412, 246, 0.08f, true, 1.0f);
            C2D_DrawRectSolid(0,0,0.32f,400,240,color(0,0,0,105));
            drawPanel(52 + uiShift, 72, 296, 100, accent, 0.80f);
            drawText("W.I.T.C.H. TETRIS", 92 + uiShift, 93, 0.70f, accent);
            drawText("THE GAME HAS BEGUN.", 104 + uiShift, 132, 0.41f, text);
        }
    }

    C2D_TargetClear(bottom, color(12,9,20));
    C2D_SceneBegin(bottom);
    drawText("ORIGINAL INTRO — RANDOMIZED", 10, 14, 0.45f, accent);
    if (scene == 5) {
        drawText(intro.transformAll ? "TRANSFORM MODE: ALL CHARACTERS"
                                    : std::string("TRANSFORM MODE: ") + PIECE_CHARACTERS[intro.transformKind],
                 10, 55, 0.34f, text);
        drawText("50% ALL / 50% ONE RANDOM CHARACTER", 10, 78, 0.30f, accent);
    } else {
        drawText("The random branch is rerolled on every replay.", 10, 58, 0.32f, text);
    }
    C2D_DrawRectSolid(12, 114, 0.75f, 296, 48, color(88,45,118,230));
    drawText("A / TOUCH — NEXT SCENE", 50, 128, 0.44f, text);
    drawText("B / START — skip to menu", 10, 174, 0.40f, text);
    char buf[40];
    std::snprintf(buf, sizeof(buf), "SCENE %d / 8", scene + 1);
    drawText(buf, 10, 211, 0.38f, accent);
}

float clamp01(float v) {
    return std::max(0.0f, std::min(1.0f, v));
}

float lerpf(float a, float b, float t) {
    return a + (b - a) * t;
}

void drawAtlasFrame(const std::string& key, int index,
                    float x, float y, float w, float h, float depth = 0.55f,
                    float alpha = 1.0f) {
    if (!g_assets.has(key)) return;
    drawImageFit(g_assets.image(key, index), x, y, w, h, depth, false, alpha);
}

void renderEnding(C3D_RenderTarget* top, C3D_RenderTarget* bottom,
                  float t, float eyeShift = 0.0f) {
    const u32 text = color(244,222,255);
    const u32 accent = color(205,140,255);

    const float bgShift = eyeShift * 1.00f;
    const float midShift = -eyeShift * 0.80f;
    const float actorShift = -eyeShift * 2.10f;
    const float frontShift = -eyeShift * 3.10f;
    const float uiShift = -eyeShift * 0.55f;

    C2D_TargetClear(top, color(0,0,0));
    C2D_SceneBegin(top);

    if (t < 14.0f) {
        const int heartFrame = static_cast<int>(t * 8.0f) % 24;
        drawAtlasFrame("ending_heart", heartFrame,
                       12 + actorShift, 38, 135, 180, 0.58f);

        static const char* credits[] = {
            "W.I.T.C.H. TETRIS",
            "DESIGN: CHAT GPT",
            "MUSIC / SOUND: SUNO",
            "DEVELOPMENT: CHAT GPT",
            "SPECIAL THANKS",
            "W.I.T.C.H. ANIMATED SERIES",
            "JETIX",
            "AND EVERYONE WHO REMEMBERS",
            "THIS STORY",
            "FAN PROJECT — NON-COMMERCIAL",
            "@art3m_k_a"
        };
        constexpr int creditCount = sizeof(credits) / sizeof(credits[0]);
        const float totalTravel = 340.0f + creditCount * 25.0f;
        const float startY = 225.0f - totalTravel * clamp01(t / 14.0f);
        for (int i=0;i<creditCount;++i) {
            const float y = startY + i * 25.0f;
            if (y > 10.0f && y < 235.0f)
                drawText(credits[i], 153 + uiShift, y,
                         i==0 ? 0.38f : 0.27f, i==0 ? accent : text);
        }
    } else if (t < 24.0f) {
        C2D_DrawRectSolid(0,0,0.10f,400,240,color(8,5,13));
        const float bt = t - 14.0f;

        if (t < 20.0f) {
            for (int i=0;i<6;++i) {
                const float x = 370.0f - bt * 28.0f + (i%3)*34.0f + midShift;
                const float y = 54.0f + (i/3)*92.0f;
                const float alpha = 1.0f - clamp01((t - 19.3f) / 0.7f);
                drawAtlasFrame("ending_enemies", i, x, y, 52, 70, 0.46f, alpha);
            }
            for (int i=0;i<6;++i) {
                const float x = 360.0f - std::fmod(bt*75.0f + i*48.0f, 330.0f) + midShift;
                const float y = 42.0f + (i%3)*35.0f;
                drawAtlasFrame("ending_bats", (static_cast<int>(t*12)+i)%6,
                               x, y, 34, 28, 0.50f);
            }
        }

        if (t >= 20.0f && t < 22.0f) {
            const float alpha = 1.0f - clamp01((t - 21.65f) / 0.35f);
            drawAtlasFrame("ending_cedric", 0,
                           293 + actorShift, 40, 92, 183, 0.52f, alpha);
        }

        const char* actorKeys[] = {
            "ending_will","ending_irma","ending_taranee",
            "ending_caleb","ending_haylin","ending_cornelia"
        };
        const float fightX[] = {48,102,154,212,267,321};
        const float finalX[] = {72,124,176,232,286,338};
        for (int i=0;i<6;++i) {
            float x=fightX[i], y=80 + (i%2)*18;
            int pose=1;
            if (t < 18.0f) {
                const float p=clamp01((t - 16.6f - i*0.12f)/1.0f);
                x=lerpf(-55.0f,fightX[i],p);
                pose=1;
            } else if (t < 22.0f) {
                x=fightX[i] + std::sin((t-18.0f)*9.0f+i)*7.0f;
                y-=std::abs(std::sin(t*7.0f+i))*8.0f;
                pose=(static_cast<int>((t-18.0f)*5.0f)+i)%6;
            } else {
                float p=clamp01((t-22.0f)/2.0f);
                p=p*p*(3.0f-2.0f*p);
                x=lerpf(fightX[i],finalX[i],p);
                y=lerpf(y,91.0f+(i%2)*10.0f,p);
                pose=0;
            }
            drawAtlasFrame(actorKeys[i], pose,
                           x-26 + actorShift, y, 52, 132,
                           i==3 ? 0.61f : 0.60f);
        }

        float bx=92, by=150;
        int bpose=0;
        if (t < 18.0f) {
            bx=260.0f-(t-14.0f)*45.0f;
            bpose=static_cast<int>(t*9.0f)%6;
        } else if (t < 22.0f) {
            bx=56; bpose=3;
        } else {
            const float p=clamp01((t-22.0f)/2.0f);
            bx=lerpf(56,118,p); bpose=0;
        }
        drawAtlasFrame("ending_blunk", bpose,
                       bx-24 + frontShift, by, 48, 72, 0.62f);

        if (t > 21.55f && t < 22.0f) {
            const float p=(t-21.55f)/0.45f;
            const int a=static_cast<int>(115.0f*std::sin(p*3.1415926f));
            C2D_DrawRectSolid(0,0,0.86f,400,240,color(230,212,255,a));
        }
    } else if (t < 26.0f) {
        drawAssetFit("ending_phobos", -6 + actorShift, -3, 412, 246,
                     0.30f, true, 1.0f);
    } else {
        const float p = clamp01((t - 26.0f) / 2.1f);
        drawAssetFit("ending_witch", -6 + bgShift, -3, 412, 246,
                     0.30f, true, 1.0f);
        drawAssetFit("ending_phobos", -6 + actorShift, -3, 412, 246,
                     0.50f, true, 1.0f-p);

        if (p < 1.0f) {
            for (int i=0;i<32;++i) {
                const float delay=(i%7)*0.055f;
                const float q=clamp01((p-delay)/std::max(0.01f,1.0f-delay));
                if(q>=1.0f) continue;
                const float x=185.0f+(i%8)*8.0f + ((i%3)-1)*24.0f*q + frontShift;
                const float y=35.0f+(i/8)*32.0f - (36.0f+(i%5)*8.0f)*q;
                C2D_DrawRectSolid(x,y,0.72f,4,4,
                    color(170,90,210,static_cast<u8>(220*(1.0f-q))));
            }
        }

        if (t >= 28.1f) {
            drawPanel(72 + uiShift, 174, 256, 46, accent, 0.82f);
            drawText("THANK YOU FOR PLAYING", 99 + uiShift, 188, 0.48f, text);
        }
    }

    C2D_TargetClear(bottom, color(10,7,17));
    C2D_SceneBegin(bottom);
    drawText("W.I.T.C.H. ENDING — MUSIC CLOCK", 10, 13, 0.43f, accent);
    char buf[80];
    std::snprintf(buf,sizeof(buf),"TIME %.1f / 28.7 SEC",t);
    drawText(buf,10,52,0.38f,text);

    const char* beat = t < 14.0f ? "CREDITS + HEART" :
                       t < 20.0f ? "BATTLE — ENEMIES" :
                       t < 22.0f ? "BATTLE — CEDRIC" :
                       t < 24.0f ? "BATTLE — FINAL FORMATION" :
                       t < 26.0f ? "PHOBOS ART" :
                       t < 28.1f ? "DISINTEGRATION / CROSSFADE" :
                       "THANK YOU";
    drawText(beat,10,82,0.34f,accent);

    if (t >= 30.65f) {
        C2D_DrawRectSolid(12,126,0.72f,296,51,color(88,45,118,230));
        drawText("A / TOUCH — RETURN",64,142,0.45f,text);
    } else {
        drawText("The sequence follows ending.py timing.",10,132,0.32f,text);
        drawText("B / START — skip back",10,158,0.36f,text);
    }
}

void renderCutsceneMenu(C3D_RenderTarget* top, C3D_RenderTarget* bottom, int selected) {
    const u32 accent = color(210,140,255);
    const u32 text = color(240,235,248);
    C2D_TargetClear(top, color(7,6,13));
    C2D_SceneBegin(top);
    drawFullscreenAsset("bg_phase1");
    C2D_DrawRectSolid(0,0,0.25f,400,240,color(0,0,0,115));
    drawPanel(30, 22, 340, 196, accent);
    drawText("CUTSCENE ARCHIVE", 92, 38, 0.57f, accent);
    for (int i=0;i<CUTSCENE_COUNT;++i) {
        const float y=82+i*30;
        if(i==selected) C2D_DrawRectSolid(48,y-4,0.82f,305,23,color(96,50,126,220));
        drawText(std::string(i==selected?"> ":"  ")+CUTSCENE_ITEMS[i],55,y,0.39f,text);
    }

    C2D_TargetClear(bottom, color(12,9,20));
    C2D_SceneBegin(bottom);
    drawText("A — play selected scene", 12, 48, 0.44f, text);
    drawText("B / START — back", 12, 79, 0.44f, text);
    drawText("Scenes also trigger at 100 and 200 lines.", 12, 137, 0.38f, accent);
}

void renderCutscene(C3D_RenderTarget* top, C3D_RenderTarget* bottom,
                    const CutsceneState& cs, float elapsedSeconds,
                    float eyeShift = 0.0f) {
    if (cs.kind == CutsceneKind::Ending) {
        renderEnding(top,bottom,elapsedSeconds,eyeShift);
        return;
    }

    const u32 accent=color(211,143,255), text=color(245,240,250);
    const float bgShift = eyeShift * 1.15f;
    const float actorShift = -eyeShift * 2.25f;
    const float uiShift = -eyeShift * 0.60f;

    C2D_TargetClear(top,color(4,3,8));
    C2D_SceneBegin(top);

    std::string title;
    int total=1;

    if(cs.kind==CutsceneKind::Lines100) {
        title="100 LINES — RESISTANCE";
        const char* frames[]={"l100_phobos","l100_will","l100_cornelia","l100_irma",
                              "l100_taranee","l100_haylin","l100_caleb","l100_heart"};
        total=8;
        drawAssetFit("bg_phase1",-6+bgShift,-3,412,246,0.08f,true,1.0f);
        C2D_DrawRectSolid(0,0,0.25f,400,240,color(0,0,0,75));
        drawAssetFit(frames[cs.frame%total],70+actorShift,18,260,205,0.55f);
    } else if(cs.kind==CutsceneKind::Lines200) {
        title="200 LINES — PHOBOS COLLAPSES";
        total=6;
        drawAssetFit("bg_phase2",-6+bgShift,-3,412,246,0.08f,true,1.0f);
        C2D_DrawRectSolid(0,0,0.25f,400,240,color(0,0,0,75));
        char key[32];
        std::snprintf(key,sizeof(key),"l200_collapse_%d",cs.frame%6);
        drawAssetFit(key,40+actorShift,10,320,220,0.55f);
    } else {
        title="CUTSCENE";
        total=1;
    }
    drawPanel(8+uiShift,5,384,29,accent,0.80f);
    drawText(title,20+uiShift,12,0.38f,text);

    C2D_TargetClear(bottom,color(12,9,20));
    C2D_SceneBegin(bottom);
    drawText(title,12,16,0.47f,accent);
    char buf[64];
    std::snprintf(buf,sizeof(buf),"FRAME %d / %d",cs.frame+1,total);
    drawText(buf,12,62,0.40f,text);
    C2D_DrawRectSolid(12,112,0.75f,296,50,color(88,45,118,230));
    drawText("A / TOUCH — NEXT",67,128,0.46f,text);
    drawText("B / START — leave scene",12,174,0.40f,text);
    drawText("Stereo depth: background -> actors -> UI.",12,210,0.34f,accent);
}

enum class MiniType {
    Snake = 0,
    Treasure,
    StoneCovers,
    DarkWater,
    Count
};

const char* MINI_NAMES[] = {
    "SNAKE — BLUNK/CEDRIC/PHOBOS",
    "BLUNK TREASURE ESCAPE",
    "CORNELIA STONE COVERS",
    "IRMA DARK WATER PANIC"
};

struct Drop {
    int lane;
    float y;
    bool active;
    Drop(int l = 0, float py = 0.0f, bool a = false) : lane(l), y(py), active(a) {}
};

class MiniGame {
public:
    MiniGame() : rng_(static_cast<unsigned int>(osGetTime() ^ 0x51A7u)) { reset(MiniType::Snake); }

    void reset(MiniType type) {
        type_=type; score_=0; lives_=(type==MiniType::Snake?1:3); over_=false; tick_=0;
        dir_={1,0}; nextDir_={1,0};
        snake_.clear(); snake_.push_back({5,7}); snake_.push_back({4,7}); snake_.push_back({3,7});
        food_={14,7}; snakeVariant_=static_cast<int>(rng_()%4==0?2:(rng_()%3==0?1:0));

        treasurePos_=0; treasureCedric_=6.0f; treasureCarry_=false; treasureSafe_=60;

        cover_=1; dangerLane_=static_cast<int>(rng_()%4); dangerTimer_=100;

        waterLane_=2; waterStored_=0; waterDrop_=Drop(static_cast<int>(rng_()%5), 15.0f, true);
    }

    MiniType type() const { return type_; }
    int score() const { return score_; }
    int lives() const { return lives_; }
    bool over() const { return over_; }

    void handle(u32 down) {
        if (over_) {
            if (down & KEY_A) reset(type_);
            return;
        }

        if (type_ == MiniType::Snake) {
            Point d=nextDir_;
            if(down&KEY_LEFT) d={-1,0};
            else if(down&KEY_RIGHT) d={1,0};
            else if(down&KEY_UP) d={0,-1};
            else if(down&KEY_DOWN) d={0,1};
            if(!(d.x==-dir_.x && d.y==-dir_.y)) nextDir_=d;
        } else if (type_ == MiniType::Treasure) {
            if(down&KEY_LEFT) treasurePos_=std::max(0,treasurePos_-1);
            if(down&KEY_RIGHT) treasurePos_=std::min(6,treasurePos_+1);
            if(treasurePos_==6) treasureCarry_=true;
            if(treasureCarry_ && treasurePos_==0) {
                score_+=10; treasureCarry_=false; treasureCedric_=6.0f; treasureSafe_=45;
            }
        } else if (type_ == MiniType::StoneCovers) {
            if(down&KEY_LEFT) cover_=std::max(0,cover_-1);
            if(down&KEY_RIGHT) cover_=std::min(3,cover_+1);
        } else if (type_ == MiniType::DarkWater) {
            if(down&KEY_LEFT) waterLane_=std::max(0,waterLane_-1);
            if(down&KEY_RIGHT) waterLane_=std::min(4,waterLane_+1);
            if((down&(KEY_A|KEY_X)) && waterStored_==3) {
                score_+=15; waterStored_=0;
            }
        }
    }

    void update() {
        if(over_) return;
        ++tick_;

        if(type_==MiniType::Snake) {
            const int speed=std::max(4,10-score_/25);
            if(tick_%speed==0) {
                dir_=nextDir_;
                Point h=snake_.front();
                Point n={(h.x+dir_.x+20)%20,(h.y+dir_.y+14)%14};
                if(std::find_if(snake_.begin(),snake_.end(),[&](const Point& p){return p.x==n.x&&p.y==n.y;})!=snake_.end()) {
                    lives_=0; over_=true; return;
                }
                snake_.insert(snake_.begin(),n);
                if(n.x==food_.x && n.y==food_.y) {
                    score_+=5;
                    food_={static_cast<int>(rng_()%20),static_cast<int>(rng_()%14)};
                } else snake_.pop_back();
            }
        } else if(type_==MiniType::Treasure) {
            if(treasureSafe_>0) --treasureSafe_;
            const int pace=std::max(12,34-score_/5);
            if(treasureSafe_==0 && tick_%pace==0) {
                if(treasureCedric_>treasurePos_) treasureCedric_-=1.0f;
                else if(treasureCedric_<treasurePos_) treasureCedric_+=1.0f;
                if(static_cast<int>(treasureCedric_+0.5f)==treasurePos_) {
                    --lives_; treasureCarry_=false; treasurePos_=0; treasureCedric_=6.0f; treasureSafe_=75;
                    if(lives_<=0) over_=true;
                }
            }
        } else if(type_==MiniType::StoneCovers) {
            --dangerTimer_;
            if(dangerTimer_<=0) {
                if(cover_==dangerLane_) score_+=2;
                else if(--lives_<=0) over_=true;
                dangerLane_=static_cast<int>(rng_()%4);
                dangerTimer_=std::max(28,95-score_/3);
            }
        } else if(type_==MiniType::DarkWater) {
            const int level=tick_/(18*FPS);
            const float speed=0.75f+level*0.16f;
            if(!waterDrop_.active) {
                waterDrop_=Drop(static_cast<int>(rng_()%5),18.0f,true);
            }
            waterDrop_.y+=speed;
            if(waterDrop_.y>=190.0f) {
                if(waterDrop_.lane==waterLane_ && waterStored_<3) ++waterStored_;
                else if(--lives_<=0) over_=true;
                waterDrop_.active=false;
            }
        }
    }

    void renderTop(C3D_RenderTarget* target) const {
        const u32 accent=color(210,140,255), text=color(245,240,250);
        C2D_TargetClear(target,color(10,7,18));
        C2D_SceneBegin(target);
        drawFullscreenAsset("bg_phase1");
        C2D_DrawRectSolid(0,0,0.2f,400,240,color(0,0,0,125));
        drawPanel(18,18,364,204,accent);

        drawText(MINI_NAMES[static_cast<int>(type_)],30,27,0.40f,accent);

        char hud[80];
        std::snprintf(hud,sizeof(hud),"SCORE %d    LIFE %d",score_,lives_);
        drawText(hud,270,28,0.31f,text);

        if(type_==MiniType::Snake) renderSnake();
        else if(type_==MiniType::Treasure) renderTreasure();
        else if(type_==MiniType::StoneCovers) renderStone();
        else renderWater();

        if(over_) {
            drawPanel(82,82,236,83,color(230,80,100),0.85f);
            drawText("GAME OVER",125,100,0.63f,color(245,100,120));
            drawText("A — retry",154,135,0.40f,text);
        }
    }

    void renderBottom(C3D_RenderTarget* target) const {
        const u32 accent=color(210,140,255), text=color(240,235,248);
        C2D_TargetClear(target,color(12,9,20));
        C2D_SceneBegin(target);
        drawText("MINI-GAME PORT",12,14,0.50f,accent);
        if(type_==MiniType::Snake) {
            drawText("D-Pad — direction",12,62,0.44f,text);
            drawText("Eat the target. Do not hit yourself.",12,94,0.37f,text);
        } else if(type_==MiniType::Treasure) {
            drawText("← → — fixed positions",12,62,0.44f,text);
            drawText("Take treasure at right; bank it at left.",12,94,0.37f,text);
        } else if(type_==MiniType::StoneCovers) {
            drawText("← → — move Cornelia's stone cover",12,62,0.40f,text);
            drawText("Be under the flashing danger lane.",12,94,0.37f,text);
        } else {
            drawText("← → — move Irma's vessel",12,62,0.42f,text);
            drawText("A / X — dump when 3 drops are stored",12,94,0.37f,text);
        }
        drawText("START / B — back to mini-game menu",12,185,0.37f,accent);
        drawText("A — retry after Game Over",12,211,0.34f,text);
    }

private:
    MiniType type_=MiniType::Snake;
    int score_=0,lives_=1,tick_=0;
    bool over_=false;
    std::mt19937 rng_;

    Point dir_{1,0},nextDir_{1,0};
    std::vector<Point> snake_;
    Point food_{14,7};
    int snakeVariant_=0;

    int treasurePos_=0;
    float treasureCedric_=6.0f;
    bool treasureCarry_=false;
    int treasureSafe_=0;

    int cover_=1,dangerLane_=0,dangerTimer_=100;

    int waterLane_=2,waterStored_=0;
    Drop waterDrop_;

    void drawIcon(const std::string& key,float cx,float cy,float size) const {
        if(g_assets.has(key)) drawAssetFit(key,cx-size/2,cy-size/2,size,size,0.64f);
        else C2D_DrawCircleSolid(cx,cy,0.64f,size*0.35f,color(210,140,255));
    }

    void renderSnake() const {
        const float ox=42,oy=61,cw=15,ch=10;
        C2D_DrawRectSolid(ox,oy,0.42f,300,140,color(8,8,16,220));
        for(size_t i=0;i<snake_.size();++i) {
            const Point& p=snake_[i];
            const float x=ox+p.x*cw,y=oy+p.y*ch;
            if(i==0) {
                const char* key=snakeVariant_==0?"mg_blunk":(snakeVariant_==1?"mg_cedric":"mg_phobos");
                drawIcon(key,x+cw/2,y+ch/2,18);
            } else C2D_DrawRectSolid(x+2,y+2,0.6f,cw-4,ch-4,
                snakeVariant_==0?color(224,183,54):(snakeVariant_==1?color(75,170,90):color(80,50,110)));
        }
        const float fx=ox+food_.x*cw+cw/2,fy=oy+food_.y*ch+ch/2;
        if(snakeVariant_==2) drawIcon("mg_heart",fx,fy,16);
        else if(snakeVariant_==1) drawIcon("mg_phobos",fx,fy,16);
        else C2D_DrawCircleSolid(fx,fy,0.65f,5,color(250,210,70));
    }

    void renderTreasure() const {
        const float y=136;
        for(int i=0;i<7;++i) {
            const float x=55+i*48;
            C2D_DrawCircleSolid(x,y,0.5f,8,i==treasurePos_?color(220,145,255):color(95,70,115));
        }
        drawIcon("mg_blunk",55+treasurePos_*48,y-25,44);
        drawIcon("mg_cedric",55+treasureCedric_*48,y+28,48);
        C2D_DrawCircleSolid(55+6*48,83,0.6f,10,color(250,205,60));
        drawText(treasureCarry_?"TREASURE: CARRIED":"TREASURE: VAULT",45,188,0.38f,color(245,240,250));
    }

    void renderStone() const {
        const char* labels[]={"WILL","IRMA","TARANEE","HAY LIN"};
        const char* keys[]={"mg_will","mg_irma","",""};
        for(int i=0;i<4;++i) {
            const float x=68+i*88;
            C2D_DrawRectSolid(x-28,91,0.46f,56,73,color(35,25,47,230));
            if(keys[i][0]) drawIcon(keys[i],x,116,48);
            else drawText(labels[i],x-25,108,0.28f,color(240,235,248));
            if(i==cover_) C2D_DrawRectSolid(x-30,157,0.64f,60,12,color(145,110,82));
            if(i==dangerLane_) {
                const float pulse=static_cast<float>(std::max(0,dangerTimer_))/100.0f;
                C2D_DrawTriangle(x,68,color(245,80,90),x-9,84,color(245,80,90),x+9,84,color(245,80,90),0.7f);
                (void)pulse;
            }
        }
        drawText("CORNELIA'S STONE SHIELD",102,187,0.36f,color(210,140,255));
    }

    void renderWater() const {
        const float ox=70,spacing=65,bottom=190;
        for(int i=0;i<5;++i) {
            const float x=ox+i*spacing;
            C2D_DrawLine(x,67,color(80,90,130),x,bottom,color(80,90,130),1.0f,0.45f);
        }
        if(waterDrop_.active) {
            const float x=ox+waterDrop_.lane*spacing;
            C2D_DrawCircleSolid(x,waterDrop_.y,0.65f,7,color(80,50,130));
        }
        const float px=ox+waterLane_*spacing;
        drawIcon("mg_irma",px,bottom,42);
        C2D_DrawRectSolid(px-18,bottom+19,0.68f,36,10,color(70,145,205));
        char buf[48];
        std::snprintf(buf,sizeof(buf),"VESSEL %d / 3",waterStored_);
        drawText(buf,150,198,0.36f,color(245,240,250));
    }
};

void renderMiniMenu(C3D_RenderTarget* top,C3D_RenderTarget* bottom,int selected) {
    const u32 accent=color(210,140,255),text=color(240,235,248);
    C2D_TargetClear(top,color(8,6,14));
    C2D_SceneBegin(top);
    drawFullscreenAsset("bg_phase1");
    C2D_DrawRectSolid(0,0,0.2f,400,240,color(0,0,0,120));
    drawPanel(22,18,356,206,accent);
    drawText("MINI-GAMES — PHASE 2",78,34,0.53f,accent);
    for(int i=0;i<static_cast<int>(MiniType::Count);++i) {
        const float y=83+i*31;
        if(i==selected) C2D_DrawRectSolid(40,y-5,0.8f,320,24,color(100,52,130,220));
        drawText(std::string(i==selected?"> ":"  ")+MINI_NAMES[i],47,y,0.36f,text);
    }
    drawText("More original mini-games follow after hardware profiling.",42,207,0.28f,accent);

    C2D_TargetClear(bottom,color(12,9,20));
    C2D_SceneBegin(bottom);
    drawText("FOUR PLAYABLE PORTS IN THIS BUILD",12,18,0.45f,accent);
    drawText("Snake keeps the Blunk/Cedric/Phobos variants.",12,61,0.35f,text);
    drawText("Treasure Escape uses fixed Game & Watch positions.",12,86,0.35f,text);
    drawText("Stone Covers preserves the four-lane shield rule.",12,111,0.35f,text);
    drawText("Dark Water uses 5 lanes + 3-drop vessel.",12,136,0.35f,text);
    drawText("A — start     B / START — menu",12,207,0.38f,accent);
}

void renderPhobosRoom(C3D_RenderTarget* top,C3D_RenderTarget* bottom,
                      int state,float eyeShift=0.0f) {
    const u32 accent=color(210,140,255),text=color(245,240,250);

    // Match desktop v6.37.1: room composite -> seated Phobos -> repaint the
    // lower portion of that SAME composite. No separately scaled table sprite.
    const float bgShift = eyeShift * 1.15f;
    const float phobosShift = -eyeShift * 2.10f;
    const float deskShift = -eyeShift * 3.05f;

    C2D_TargetClear(top,color(5,3,8));
    C2D_SceneBegin(top);

    drawAssetFit("phobos_room_bg",-6+bgShift,-3,412,246,0.08f,true,1.0f);
    C2D_DrawRectSolid(0,0,0.20f,400,240,color(0,0,0,18));

    char key[40];
    std::snprintf(key,sizeof(key),"phobos_room_pose%d",state%6);
    // Desktop pose is ~565/1080 of the canvas and bottoms around y=900.
    // The 3DS equivalent is ~126 px tall with the body disappearing behind desk.
    drawAssetFit(key,100+phobosShift,66,200,134,0.53f,false,1.0f);

    // Exact lower repaint generated from background_v2 at the desktop 700/1080
    // split, so the desk/window geometry aligns pixel-for-pixel.
    drawAssetFit("phobos_room_foreground",-6+deskShift,-3,412,246,
                 0.72f,true,1.0f);

    C2D_TargetClear(bottom,color(8,5,13));
    C2D_SceneBegin(bottom);

    drawPanel(9,12,302,158,accent,0.30f);
    drawText("ФОБОС",20,24,0.43f,accent);
    drawText("Левый Shift?",20,67,0.37f,text);
    drawText("Раньше он мог быть HOLD.",20,94,0.34f,text);

    C2D_DrawRectSolid(12,181,0.66f,140,38,color(88,45,118,225));
    drawText("A / TOUCH: NEXT",27,193,0.34f,text);
    drawText("X: POSE",177,187,0.30f,accent);
    drawText("B / START: MENU",177,208,0.28f,text);

    char buf[48];
    std::snprintf(buf,sizeof(buf),"POSE %d / 6",state+1);
    drawText(buf,18,223,0.25f,color(176,125,205));
}

void handleHorizontalRepeat(Game& game,u32 down,u32 held,int& repeatDir,int& repeatTimer) {
    int dir=0;
    if(held&KEY_LEFT) dir=-1;
    else if(held&KEY_RIGHT) dir=1;
    if((down&KEY_LEFT)||(down&KEY_RIGHT)) {
        repeatDir=dir; repeatTimer=12; if(dir) game.move(dir,0); return;
    }
    if(dir==0) {repeatDir=0;repeatTimer=0;return;}
    if(dir!=repeatDir) {repeatDir=dir;repeatTimer=12;game.move(dir,0);return;}
    if(repeatTimer>0) --repeatTimer;
    else {game.move(dir,0);repeatTimer=3;}
}

std::string musicForMini(MiniType type) {
    switch(type) {
        case MiniType::Snake: return "romfs:/audio/minigame_snake.mp3";
        case MiniType::Treasure: return "romfs:/audio/minigame_treasure.mp3";
        case MiniType::StoneCovers: return "romfs:/audio/minigame_stone.mp3";
        case MiniType::DarkWater: return "romfs:/audio/minigame_water.mp3";
        default: return "romfs:/audio/minigame_arcade.mp3";
    }
}

std::vector<std::string> musicPoolForTetris(int lines, bool phobosRoute = false) {
    if(lines>=200) {
        if(phobosRoute) {
            return {
                "romfs:/audio/phase2_phobos.mp3",
                "romfs:/audio/music_empty_hollow_1.mp3",
                "romfs:/audio/music_empty_hollow_2.mp3",
                "romfs:/audio/music_crucified.mp3",
                "romfs:/audio/music_crusified2.mp3",
                "romfs:/audio/music_blunk_snake.mp3",
                "romfs:/audio/music_snake_4.mp3",
                "romfs:/audio/music_washing_4.mp3",
                "romfs:/audio/music_arcade_6.mp3"
            };
        }
        return {
            "romfs:/audio/phase2_guardians.mp3",
            "romfs:/audio/music_cutscene_guardians_win.mp3",
            "romfs:/audio/music_arcade_5.mp3",
            "romfs:/audio/music_bonus_2.mp3",
            "romfs:/audio/music_snake_3.mp3",
            "romfs:/audio/music_washing_3.mp3",
            "romfs:/audio/music_football_2.mp3"
        };
    }
    if(lines>=100) {
        return {
            "romfs:/audio/phase1_1.mp3",
            "romfs:/audio/phase1_2.mp3",
            "romfs:/audio/phase1_3.mp3",
            "romfs:/audio/music_phase1_hollow.mp3",
            "romfs:/audio/music_cutscene_lines100_football.mp3",
            "romfs:/audio/music_arcade_2.mp3",
            "romfs:/audio/music_arcade_4.mp3",
            "romfs:/audio/music_collection_minigames_2.mp3",
            "romfs:/audio/music_snake_2.mp3",
            "romfs:/audio/music_washing_2.mp3",
            "romfs:/audio/music_football_1.mp3"
        };
    }
    return {
        "romfs:/audio/phase0.mp3",
        "romfs:/audio/music_arcade_1.mp3",
        "romfs:/audio/music_arcade_3.mp3",
        "romfs:/audio/music_arcade_6.mp3",
        "romfs:/audio/music_collection_minigames_1.mp3",
        "romfs:/audio/music_bonus_1.mp3",
        "romfs:/audio/music_snake_1.mp3",
        "romfs:/audio/music_washing_1.mp3"
    };
}

std::string musicForTetris(int lines, bool phobosRoute = false) {
    const std::vector<std::string> pool=musicPoolForTetris(lines,phobosRoute);
    return pool.empty()?std::string():pool.front();
}

} // namespace

int main() {
    gfxInitDefault();
    gfxSet3D(true);
    romfsInit();
    C3D_Init(C3D_DEFAULT_CMDBUF_SIZE);
    C2D_Init(C2D_DEFAULT_MAX_OBJECTS);
    C2D_Prepare();

    initColors();
    initShapes();

    C3D_RenderTarget* topLeft=C2D_CreateScreenTarget(GFX_TOP,GFX_LEFT);
    C3D_RenderTarget* topRight=C2D_CreateScreenTarget(GFX_TOP,GFX_RIGHT);
    C3D_RenderTarget* bottom=C2D_CreateScreenTarget(GFX_BOTTOM,GFX_LEFT);
    g_textBuf=C2D_TextBufNew(8192);

    Mp3Player audio(0);
    Mp3Player voiceAudio(1);
    audio.init();
    voiceAudio.init();

    Game game;
    Mode mode=Mode::Intro;
    CutsceneState cutscene;
    IntroState intro;
    std::mt19937 uiRng(static_cast<unsigned int>(osGetTime() ^ 0x57495443u));
    rerollIntro(intro, uiRng);

    CodeKeyboardState codes;
    int menuIndex=0;
    int cutsceneIndex=0;
    int phobosState=0;
    int routeChoice=0;
    int settingsPage=0;
    int settingsIndex=0;
    int repeatDir=0,repeatTimer=0;
    bool shown100=false,shown200=false,shown300=false;
    bool guardiansRoute=false,phobosRoute=false;
    bool quit=false;

    bool voiceTakeover=false;
    std::deque<std::string> voiceFollowups;

    // Original desktop reaction state. The 18 s global cooldown keeps Phobos
    // alive without letting him talk over every move.
    int reactionCooldown=0;
    int reactionRotationCount=0;
    int reactionRotationBlockPieces=0;
    int reactionHoldCount=0;
    int reactionPlayFrames=0;
    int reactionPauseEligibleAt=FPS*(150+static_cast<int>(uiRng()%271));
    bool reactionPauseHintPlayed=false;
    bool reactionGameOverHandled=false;
    bool reactionLayoutDone=false;
    int consecutiveGameOvers=0;
    bool loserStreakVoiceUsed=false;
    int observedPieceSerial=game.pieceSerial();
    int observedClearSerial=game.clearEventSerial();
    std::set<std::string> spawnReactionUsed;
    std::set<std::string> pauseReactionUsed;

    // L/R music selection is scoped to the current gameplay music pool.
    int manualMusicPhase=-999;
    int manualMusicIndex=0;

    auto setMusic=[&](const std::string& path,bool loop=true){
        if(audio.ready() && !path.empty() &&
           (audio.path()!=path || !audio.playing()))
            audio.play(path,loop);
    };

    auto playVoice=[&](const std::string& voicePath)->bool {
        if(!voiceAudio.ready() || voicePath.empty() || voiceTakeover) return false;
        if(!voiceAudio.play(voicePath,false)) return false;
        voiceTakeover=true;
        audio.setVolume(0.30f);
        return true;
    };

    auto gameplayMusicKey=[&]()->int {
        if(codes.vtdMode) return 30;
        if(game.lines()>=200) return phobosRoute?21:20;
        if(game.lines()>=100) return 10;
        return 0;
    };

    auto gameplayMusicPool=[&]()->std::vector<std::string> {
        if(codes.vtdMode)
            return {"romfs:/audio/vtd_1.mp3","romfs:/audio/vtd_2.mp3"};
        return musicPoolForTetris(game.lines(),phobosRoute);
    };

    auto phaseOrSecretMusic=[&]()->std::string {
        const int key=gameplayMusicKey();
        std::vector<std::string> pool=gameplayMusicPool();
        if(pool.empty()) return std::string();
        if(key!=manualMusicPhase) {
            manualMusicPhase=key;
            manualMusicIndex=static_cast<int>(uiRng()%pool.size());
        }
        manualMusicIndex%=static_cast<int>(pool.size());
        if(manualMusicIndex<0) manualMusicIndex+=static_cast<int>(pool.size());
        return pool[manualMusicIndex];
    };

    auto startGameplayMusic=[&](bool forceNew=false){
        std::vector<std::string> pool=gameplayMusicPool();
        if(pool.empty()) return;
        const int key=gameplayMusicKey();
        const bool phaseChanged = key!=manualMusicPhase;
        if(phaseChanged) {
            manualMusicPhase=key;
            manualMusicIndex=static_cast<int>(uiRng()%pool.size());
            forceNew=true;
        } else if(!audio.playing() && !forceNew && pool.size()>1) {
            int next=manualMusicIndex;
            while(next==manualMusicIndex)
                next=static_cast<int>(uiRng()%pool.size());
            manualMusicIndex=next;
        }
        if(forceNew || !audio.playing()) {
            manualMusicIndex%=static_cast<int>(pool.size());
            if(manualMusicIndex<0) manualMusicIndex+=static_cast<int>(pool.size());
            audio.play(pool[manualMusicIndex],false);
        }
    };

    auto advanceGameplayMusic=[&](int delta){
        std::vector<std::string> pool=gameplayMusicPool();
        if(pool.empty()) return;
        const int key=gameplayMusicKey();
        if(key!=manualMusicPhase) {
            manualMusicPhase=key;
            manualMusicIndex=static_cast<int>(uiRng()%pool.size());
        } else if(pool.size()>1) {
            if(delta==0) {
                int next=manualMusicIndex;
                while(next==manualMusicIndex)
                    next=static_cast<int>(uiRng()%pool.size());
                manualMusicIndex=next;
            } else {
                const int n=static_cast<int>(pool.size());
                manualMusicIndex=(manualMusicIndex+delta)%n;
                if(manualMusicIndex<0) manualMusicIndex+=n;
            }
        }
        audio.play(pool[manualMusicIndex],false);
    };

    auto goMenu=[&](){
        mode=Mode::Menu;
        menuIndex=0;
        codes.open=false;
        codes.vtdMode=false;
        voiceTakeover=false;
        voiceAudio.stop();
        audio.setVolume(1.0f);
        voiceFollowups.clear();
        manualMusicPhase=-999;
        setMusic((osGetTime()/1000)%2?"romfs:/audio/menu_1.mp3":"romfs:/audio/menu_2.mp3",true);
    };

    auto startCutscene=[&](CutsceneKind kind,Mode ret){
        cutscene.kind=kind;
        cutscene.frame=0;
        cutscene.returnMode=ret;
        cutscene.startedMs=osGetTime();
        mode=Mode::Cutscene;
        codes.open=false;
        if(kind==CutsceneKind::Ending)
            audio.play("romfs:/audio/ending_outro.mp3",false);
        else if(kind==CutsceneKind::Lines100)
            audio.play("romfs:/audio/music_cutscene_lines100.mp3",true);
        else if(kind==CutsceneKind::Lines200)
            audio.play("romfs:/audio/music_cutscene_lines200.mp3",true);
    };

    auto endsWith=[](const std::string& value,const std::string& suffix)->bool {
        return value.size()>=suffix.size() &&
               value.compare(value.size()-suffix.size(),suffix.size(),suffix)==0;
    };

    auto codeMessage=[&](const std::string& msg){
        codes.message=msg;
        codes.messageFrames=180;
    };

    auto roll=[&](float probability)->bool {
        std::uniform_real_distribution<float> d(0.0f,1.0f);
        return d(uiRng)<probability;
    };

    auto randomVoice=[&](const std::vector<std::string>& pool)->std::string {
        if(pool.empty()) return std::string();
        std::uniform_int_distribution<int> d(0,static_cast<int>(pool.size())-1);
        return pool[d(uiRng)];
    };

    auto playReaction=[&](const std::string& path,const std::string& label,
                          bool ignoreCooldown=false)->bool {
        if(voiceTakeover) return false;
        if(!ignoreCooldown && reactionCooldown>0) return false;
        if(!playVoice(path)) return false;
        reactionCooldown=FPS*18;
        codeMessage(label);
        return true;
    };

    auto resetRunReactions=[&](){
        reactionCooldown=0;
        reactionRotationCount=0;
        reactionRotationBlockPieces=0;
        reactionHoldCount=0;
        reactionPlayFrames=0;
        reactionPauseEligibleAt=FPS*(150+static_cast<int>(uiRng()%271));
        reactionPauseHintPlayed=false;
        reactionGameOverHandled=false;
        reactionLayoutDone=false;
        spawnReactionUsed.clear();
        pauseReactionUsed.clear();
        observedPieceSerial=std::max(0,game.pieceSerial()-1);
        observedClearSerial=game.clearEventSerial();
    };

    auto maybeOpeningReaction=[&](){
        // Desktop v6.37.1: 65% chance, then 25/25/24/9/8/9 weighted pool.
        if(!roll(0.65f)) return;
        const int pick=static_cast<int>(uiRng()%100);
        std::string path;
        if(pick<25) path="romfs:/audio/react_start_meridian.mp3";
        else if(pick<50) path="romfs:/audio/react_start_dark.mp3";
        else if(pick<74) path="romfs:/audio/react_start_lets_begin.mp3";
        else if(pick<83) path="romfs:/audio/react_start_power.mp3";
        else if(pick<91) path="romfs:/audio/react_start_last_hope.mp3";
        else path="romfs:/audio/react_start_new_era.mp3";
        playReaction(path,"PHOBOS — START",true);
    };

    auto onceSpawn=[&](const std::string& key,float probability,
                       const std::string& path,const std::string& label)->bool {
        if(spawnReactionUsed.count(key) || reactionCooldown>0 || voiceTakeover)
            return false;
        if(!roll(probability)) return false;
        if(playReaction(path,label,false)) {
            spawnReactionUsed.insert(key);
            return true;
        }
        return false;
    };

    auto maybeSpawnReaction=[&](int kind){
        if(reactionCooldown>0 || voiceTakeover) return;

        if(kind==T) {
            if(onceSpawn("caleb_name_traitors",0.045f,
                         "romfs:/audio/react_name_traitors.mp3","PHOBOS — CALEB"))
                return;
            onceSpawn("caleb_rebel",0.025f,
                      "romfs:/audio/react_caleb_rebel.mp3","PHOBOS — REBEL");
        } else if(kind==O) {
            std::vector<std::string> choices;
            if(!spawnReactionUsed.count("blunk_angry"))
                choices.push_back("romfs:/audio/react_blunk_angry.mp3");
            if(!spawnReactionUsed.count("blunk_annoyed"))
                choices.push_back("romfs:/audio/react_blunk_annoyed.mp3");
            if(!choices.empty() && roll(0.035f)) {
                const std::string path=randomVoice(choices);
                if(playReaction(path,"PHOBOS — BLUNK",false))
                    spawnReactionUsed.insert(
                        path.find("angry")!=std::string::npos ? "blunk_angry" : "blunk_annoyed");
            }
        } else if(kind==Z) {
            if(onceSpawn("will_need_crystal",0.045f,
                         "romfs:/audio/react_need_crystal.mp3","PHOBOS — WILL"))
                return;
            if(onceSpawn("will_crystal",0.045f,
                         "romfs:/audio/react_will_crystal.mp3","PHOBOS — CRYSTAL"))
                return;
            onceSpawn("well_girls",0.018f,
                      "romfs:/audio/react_well_girls.mp3","PHOBOS — GUARDIANS");
        } else if(kind==I || kind==L || kind==J || kind==S) {
            if(onceSpawn("well_girls",0.018f,
                         "romfs:/audio/react_well_girls.mp3","PHOBOS — GUARDIANS"))
                return;
            onceSpawn("guardian_of_veil",0.008f,
                      "romfs:/audio/react_guardian.mp3","PHOBOS — GUARDIAN");
        }
    };

    auto observeSpawn=[&](){
        const int serial=game.pieceSerial();
        if(serial==observedPieceSerial) return;
        const int delta=std::max(1,std::abs(serial-observedPieceSerial));
        for(int i=0;i<delta && reactionRotationBlockPieces>0;++i)
            --reactionRotationBlockPieces;
        observedPieceSerial=serial;
        reactionRotationCount=0;
        maybeSpawnReaction(game.current().kind);
    };

    auto rotateWithReaction=[&](int direction){
        ++reactionRotationCount;
        if(reactionRotationCount>=5 && reactionRotationBlockPieces<=0 && !voiceTakeover) {
            float p=0.72f;
            if(reactionRotationCount==5) p=0.12f;
            else if(reactionRotationCount==6) p=0.24f;
            else if(reactionRotationCount==7) p=0.38f;
            else if(reactionRotationCount==8) p=0.55f;
            if(roll(p) && playReaction("romfs:/audio/react_rotate_hint.mp3",
                                       "PHOBOS — ROTATE",true)) {
                reactionRotationCount=-999;
                reactionRotationBlockPieces=6;
            }
        }
        game.rotate(direction);
    };

    auto holdWithReaction=[&](){
        if(!game.hold()) return;
        ++reactionHoldCount;
        if(reactionHoldCount>=7 && roll(0.35f)) {
            if(playReaction("romfs:/audio/react_hold_hint.mp3",
                            "PHOBOS — HOLD",false))
                reactionHoldCount=0;
        }
        observeSpawn();
    };

    auto maybePauseReaction=[&](bool leaving){
        if(voiceTakeover) return;
        const float chance=leaving?0.34f:0.52f;
        if(!roll(chance)) return;

        const std::vector<std::string> pool={
            "romfs:/audio/react_pause_well.mp3",
            "romfs:/audio/react_pause_no_hurry.mp3",
            "romfs:/audio/react_pause_waiting.mp3",
            "romfs:/audio/react_pause_what_short.mp3",
            "romfs:/audio/react_pause_what_full.mp3",
            "romfs:/audio/react_pause_what_want.mp3"
        };
        std::vector<std::string> unused;
        for(const std::string& p:pool)
            if(!pauseReactionUsed.count(p)) unused.push_back(p);
        if(unused.empty()) return;

        const std::string path=randomVoice(unused);
        if(playReaction(path,leaving?"PHOBOS — RESUME":"PHOBOS — PAUSE",true))
            pauseReactionUsed.insert(path);
    };

    auto processClearReaction=[&](){
        const int serial=game.clearEventSerial();
        if(serial==observedClearSerial) return;
        observedClearSerial=serial;

        const int cleared=game.lastCleared();
        const int kind=game.lastClearKind();
        if(cleared<=0) return;

        if(cleared==4) {
            const std::vector<std::string> willPool={
                "romfs:/audio/react_will_tetris_1.mp3",
                "romfs:/audio/react_will_tetris_2.mp3",
                "romfs:/audio/react_will_tetris_3.mp3",
                "romfs:/audio/react_will_tetris_4.mp3"
            };
            if(playReaction(randomVoice(willPool),"WILL — TETRIS",true) && roll(0.55f))
                voiceFollowups.push_back("romfs:/audio/react_tetris_not_bad.mp3");
            return;
        }

        if(reactionCooldown>0 || voiceTakeover) return;

        if(roll(0.05f)) {
            playReaction("romfs:/audio/react_destroy_weak.mp3",
                         "PHOBOS — WEAK LINK",false);
            return;
        }

        std::vector<std::string> pool;
        const char* label=nullptr;
        if(kind==I) {
            pool={"romfs:/audio/react_earth_1.mp3","romfs:/audio/react_earth_2.mp3",
                  "romfs:/audio/react_earth_3.mp3"};
            label="CORNELIA — EARTH";
        } else if(kind==S) {
            pool={"romfs:/audio/react_water_1.mp3","romfs:/audio/react_water_2.mp3",
                  "romfs:/audio/react_water_3.mp3"};
            label="IRMA — WATER";
        } else if(kind==J) {
            pool={"romfs:/audio/react_fire_1.mp3","romfs:/audio/react_fire_2.mp3",
                  "romfs:/audio/react_fire_3.mp3"};
            label="TARANEE — FIRE";
        } else if(kind==L) {
            pool={"romfs:/audio/react_air_1.mp3","romfs:/audio/react_air_2.mp3",
                  "romfs:/audio/react_air_3.mp3"};
            label="HAY LIN — AIR";
        }
        if(!pool.empty()) {
            playReaction(randomVoice(pool),label?label:"GUARDIAN",false);
            return;
        }

        if(kind==T && roll(0.40f)) {
            playReaction("romfs:/audio/react_caleb_clear.mp3","CALEB — CLEAR",false);
            return;
        }

        if(kind==O) {
            if(cleared==1 && roll(0.68f)) {
                pool={"romfs:/audio/react_blunk_businessman.mp3",
                      "romfs:/audio/react_blunk_laugh.mp3",
                      "romfs:/audio/react_blunk_groan.mp3",
                      "romfs:/audio/react_blunk_fight.mp3"};
                playReaction(randomVoice(pool),"BLUNK — CLEAR",false);
            } else if(cleared==2 && roll(0.82f)) {
                pool={"romfs:/audio/react_blunk_warrior.mp3",
                      "romfs:/audio/react_blunk_treasure.mp3",
                      "romfs:/audio/react_blunk_not_afraid.mp3"};
                playReaction(randomVoice(pool),"BLUNK — DOUBLE",false);
            }
        }
    };

    auto stepGameplayMusic=[&](int delta){
        advanceGameplayMusic(delta);
        const std::vector<std::string> pool=gameplayMusicPool();
        if(pool.empty()) return;
        char msg[48];
        std::snprintf(msg,sizeof(msg),"MUSIC %d / %d",
                      manualMusicIndex+1,static_cast<int>(pool.size()));
        codeMessage(msg);
    };

    auto togglePauseWithReaction=[&](){
        const bool wasPaused=game.paused();
        game.togglePause();
        if(wasPaused!=game.paused())
            maybePauseReaction(wasPaused); // leaving=true when resuming
    };

    auto processLongPauseHint=[&](){
        if(game.paused() || game.gameOver() || codes.open) return;
        ++reactionPlayFrames;
        if(reactionPauseHintPlayed || reactionPlayFrames<reactionPauseEligibleAt) return;

        const int sinceEligible=reactionPlayFrames-reactionPauseEligibleAt;
        if(sinceEligible% (FPS*10) != 0) return;
        if(roll(0.18f) &&
           playReaction("romfs:/audio/react_pause_hint.mp3",
                        "PHOBOS — PAUSE HINT",false))
            reactionPauseHintPlayed=true;
    };

    auto processGameOverReaction=[&](){
        if(!game.gameOver() || reactionGameOverHandled) return;
        reactionGameOverHandled=true;

        // Original game stops mocking the player after the 200-line victory
        // threshold. The route system is still being expanded on 3DS, so use
        // the same line threshold here.
        if(game.lines()>=200) return;

        ++consecutiveGameOvers;
        if(consecutiveGameOvers>=5 && !loserStreakVoiceUsed) {
            if(playReaction("romfs:/audio/react_gameover_loser.mp3",
                            "PHOBOS — GAME OVER",true)) {
                loserStreakVoiceUsed=true;
                return;
            }
        }

        if(roll(0.38f))
            playReaction("romfs:/audio/react_gameover_expected.mp3",
                         "PHOBOS — GAME OVER",true);
    };

    auto activateTypedCode=[&]()->bool {
        const std::string& b=codes.buffer;

        if(endsWith(b,"PHOBOS") || endsWith(b,"ФОБОС")) {
            codeMessage("PHOBOS HEARD YOU");
            playVoice("romfs:/audio/voice_phobos.mp3");
            codes.buffer.clear();
            return true;
        }

        if(endsWith(b,"MATRIX") || endsWith(b,"МАТРИЦА")) {
            codes.matrixFrames=FPS*9;
            codeMessage("MATRIX");
            playVoice("romfs:/audio/voice_matrix.mp3");
            codes.buffer.clear();
            return true;
        }

        if(endsWith(b,"JETIX") || endsWith(b,"ДЖЕТИКС")) {
            codes.jetixFrames=FPS*6;
            codeMessage("JETIX");
            playVoice("romfs:/audio/voice_phobos.mp3");
            codes.buffer.clear();
            return true;
        }

        if(endsWith(b,"VTD") || endsWith(b,"ВТД") || endsWith(b,"ВАЛЕНТИН")) {
            codes.vtdMode=!codes.vtdMode;
            voiceTakeover=false;
            voiceAudio.stop();
            audio.setVolume(1.0f);
            voiceFollowups.clear();
            manualMusicPhase=-999;
            if(!codes.vtdMode) game.setFallMode(FigureFallMode::Classic);
            startGameplayMusic(true);
            codeMessage(codes.vtdMode?"VTD / VALENTIN ON":"VTD OFF — CLASSIC");
            codes.buffer.clear();
            return true;
        }

        if(endsWith(b,"WITCH") || endsWith(b,"GUARDIANS") || endsWith(b,"KANDRAKAR") ||
           endsWith(b,"ВИТЧ") || endsWith(b,"СТРАЖНИЦЫ") ||
           endsWith(b,"ЧАРОДЕЙКИ") || endsWith(b,"КОНДРАКАР")) {
            game.developerClearBoard();
            codeMessage("BOARD CLEARED");
            playVoice("romfs:/audio/voice_phobos.mp3");
            codes.buffer.clear();
            return true;
        }

        if(endsWith(b,"PORN") || endsWith(b,"ПОРН")) {
            codeMessage("18+ CODE RECOGNIZED");
            playVoice("romfs:/audio/voice_porn.mp3");
            codes.buffer.clear();
            return true;
        }
        return false;
    };

    setMusic("romfs:/audio/intro.mp3",false);

    while(aptMainLoop()&&!quit) {
        hidScanInput();
        const u32 down=hidKeysDown();
        const u32 held=hidKeysHeld();
        touchPosition touch{};
        const bool touchPressed=(down&KEY_TOUCH)!=0;
        if(touchPressed) hidTouchRead(&touch);

        audio.update();
        voiceAudio.update();

        if(voiceTakeover && !voiceAudio.playing()) {
            bool followupStarted=false;
            while(!voiceFollowups.empty() && !followupStarted) {
                const std::string next=voiceFollowups.front();
                voiceFollowups.pop_front();
                followupStarted=voiceAudio.play(next,false);
            }
            if(!followupStarted) {
                voiceTakeover=false;
                audio.setVolume(1.0f);
            }
        }

        if(reactionCooldown>0) --reactionCooldown;
        if(codes.messageFrames>0) --codes.messageFrames;
        if(codes.matrixFrames>0) --codes.matrixFrames;
        if(codes.jetixFrames>0) --codes.jetixFrames;

        if(mode==Mode::Intro) {
            ++intro.frames;
            if(down&(KEY_B|KEY_START)) {
                goMenu();
            } else if((down&KEY_A)||touchPressed) {
                ++intro.scene;
                intro.frames=0;
                if(intro.scene>=8) goMenu();
            }
            setMusic("romfs:/audio/intro.mp3",false);

        } else if(mode==Mode::Menu) {
            if(down&KEY_START) quit=true;
            if(down&KEY_UP) menuIndex=(menuIndex+MENU_COUNT-1)%MENU_COUNT;
            if(down&KEY_DOWN) menuIndex=(menuIndex+1)%MENU_COUNT;
            if(down&KEY_A) {
                if(menuIndex==0) {
                    game.reset();
                    shown100=false;
                    shown200=false;
                    shown300=false;
                    guardiansRoute=false;
                    phobosRoute=false;
                    codes=CodeKeyboardState();
                    voiceTakeover=false;
                    voiceAudio.stop();
                    audio.setVolume(1.0f);
                    voiceFollowups.clear();
                    manualMusicPhase=-999;
                    mode=Mode::Tetris;
                    startGameplayMusic(true);
                    resetRunReactions();
                    maybeOpeningReaction();
                } else if(menuIndex==1) {
                    settingsPage=0;
                    settingsIndex=0;
                    mode=Mode::Settings;
                } else if(menuIndex==2) {
                    mode=Mode::CutsceneMenu;
                    cutsceneIndex=0;
                } else if(menuIndex==3) {
                    mode=Mode::PhobosRoom;
                    phobosState=0;
                    setMusic("romfs:/audio/phobos_room.mp3",true);
                } else {
                    quit=true;
                }
            }

        } else if(mode==Mode::Settings) {
            if(settingsPage==0) {
                if(down&KEY_UP) settingsIndex=(settingsIndex+2)%3;
                if(down&KEY_DOWN) settingsIndex=(settingsIndex+1)%3;
                if(down&(KEY_B|KEY_START)) {
                    goMenu();
                } else if((down&(KEY_LEFT|KEY_RIGHT)) && settingsIndex==0) {
                    game.setFallMode(game.fallMode()==FigureFallMode::Classic
                                     ? FigureFallMode::Phobos
                                     : FigureFallMode::Classic);
                } else if(down&KEY_A) {
                    if(settingsIndex==0) {
                        game.setFallMode(game.fallMode()==FigureFallMode::Classic
                                         ? FigureFallMode::Phobos
                                         : FigureFallMode::Classic);
                    } else if(settingsIndex==1) {
                        settingsPage=1;
                        settingsIndex=0;
                    } else {
                        goMenu();
                    }
                }
            } else {
                const int count=PIECE_COUNT+1;
                if(down&KEY_UP) settingsIndex=(settingsIndex+count-1)%count;
                if(down&KEY_DOWN) settingsIndex=(settingsIndex+1)%count;
                if(down&(KEY_B|KEY_START)) {
                    settingsPage=0;
                    settingsIndex=1;
                } else if(down&KEY_A) {
                    if(settingsIndex==PIECE_COUNT) {
                        settingsPage=0;
                        settingsIndex=1;
                    } else {
                        const bool next=!game.pieceEnabled(settingsIndex);
                        if(!game.setPieceEnabled(settingsIndex,next))
                            codes.message="KEEP AT LEAST ONE PIECE";
                        else
                            codes.message=std::string(PIECE_CHARACTERS[settingsIndex])+
                                          (next?" ACTIVE":" DELETED");
                        codes.messageFrames=150;
                    }
                }
            }

        } else if(mode==Mode::Tetris) {
            // React to the piece that is currently on screen before processing
            // this frame's controls.
            observeSpawn();
            processGameOverReaction();
            processLongPauseHint();

            // L+R together exits VTD and explicitly returns figure fall to
            // CLASSIC. Otherwise the shoulders remain prev/next music.
            const bool vtdExitChord =
                codes.vtdMode && (held&KEY_L) && (held&KEY_R) &&
                (down&(KEY_L|KEY_R));
            if(vtdExitChord) {
                codes.vtdMode=false;
                game.setFallMode(FigureFallMode::Classic);
                voiceTakeover=false;
                voiceAudio.stop();
                audio.setVolume(1.0f);
                voiceFollowups.clear();
                manualMusicPhase=-999;
                startGameplayMusic(true);
                codeMessage("VTD OFF — CLASSIC");
            } else {
                if(down&KEY_L) stepGameplayMusic(-1);
                if(down&KEY_R) stepGameplayMusic(+1);
            }

            if(codes.open) {
                if(down&(KEY_START|KEY_SELECT)) {
                    codes.open=false;
                    codes.buffer.clear();
                    togglePauseWithReaction();
                } else if(down&KEY_B) {
                    codes.open=false;
                    codes.buffer.clear();
                }
                if(touchPressed) {
                    const std::string token=codeTouchToken(touch,codes.russian);
                    if(token=="<CLEAR>") {
                        codes.buffer.clear();
                        codeMessage("BUFFER CLEARED");
                    } else if(token=="<LANG>") {
                        codes.russian=!codes.russian;
                        codes.buffer.clear();
                        if(!reactionLayoutDone) {
                            reactionLayoutDone=true;
                            if(roll(0.08f))
                                playReaction("romfs:/audio/react_layout.mp3",
                                             "PHOBOS — LAYOUT",false);
                        }
                    } else if(token=="<CLOSE>") {
                        codes.open=false;
                        codes.buffer.clear();
                    } else if(token=="<ENTER>") {
                        if(!activateTypedCode()) codeMessage("UNKNOWN CODE");
                        codes.buffer.clear();
                    } else if(token=="Q" && !codes.russian) {
                        // CAPS Q is the 3DS equivalent of desktop Shift+Q.
                        game.developerAddLines(10);
                        codeMessage("SHIFT+Q  +10 LINES");
                    } else if(!token.empty()) {
                        codes.buffer+=token;
                        if(codes.buffer.size()>96)
                            codes.buffer.erase(0,codes.buffer.size()-96);
                        activateTypedCode();
                    }
                }
            } else {
                if(touchPressed && hitBox(touch,13,205,152,30)) {
                    codes.open=true;
                    codes.buffer.clear();
                    codes.message="CAPS READY — TAP Q FOR +10";
                    codes.messageFrames=240;
                } else {
                    if(down&(KEY_START|KEY_SELECT))
                        togglePauseWithReaction();

                    if(game.gameOver()) {
                        processGameOverReaction();
                        if(down&KEY_B) {
                            goMenu();
                        } else if(down&KEY_A) {
                            game.reset();
                            shown100=false;
                            shown200=false;
                            shown300=false;
                            guardiansRoute=false;
                            phobosRoute=false;
                            codes.vtdMode=false;
                            voiceTakeover=false;
                            voiceAudio.stop();
                            audio.setVolume(1.0f);
                            voiceFollowups.clear();
                            manualMusicPhase=-999;
                            startGameplayMusic(true);
                            resetRunReactions();
                            maybeOpeningReaction();
                        }
                    } else if(!game.paused()) {
                        handleHorizontalRepeat(game,down,held,repeatDir,repeatTimer);

                        // Up joins A/B as rotate. Y is now the ONLY hard drop.
                        if(down&KEY_A) rotateWithReaction(+1);
                        if(down&KEY_B) rotateWithReaction(-1);
                        if(down&KEY_UP) rotateWithReaction(+1);
                        if(down&KEY_X) holdWithReaction();

                        bool hardDropped=false;
                        if(down&KEY_Y) {
                            game.hardDrop();
                            hardDropped=true;
                        }
                        if(!hardDropped)
                            game.tick((held&KEY_DOWN)!=0);
                    }
                }
            }

            // A lock can happen through gravity or Y hard-drop. Recreate the
            // original line-clear / Tetris reactions after the board event.
            processClearReaction();
            observeSpawn();
            processGameOverReaction();

            if(phobosRoute && game.gameOver()) {
                mode=Mode::PhobosRoom;
                phobosState=0;
                codes.open=false;
                voiceTakeover=false;
                voiceAudio.stop();
                audio.setVolume(1.0f);
                voiceFollowups.clear();
                setMusic("romfs:/audio/phobos_room.mp3",true);
            } else {
                startGameplayMusic(false);

                if(!shown100&&game.lines()>=100) {
                    shown100=true;
                    codes.open=false;
                    startCutscene(CutsceneKind::Lines100,Mode::Tetris);
                } else if(!shown200&&game.lines()>=200) {
                    shown200=true;
                    codes.open=false;
                    startCutscene(CutsceneKind::Lines200,Mode::Tetris);
                } else if(phobosRoute && !shown300 && game.lines()>=300) {
                    shown300=true;
                    mode=Mode::PhobosRoom;
                    phobosState=0;
                    codes.open=false;
                    setMusic("romfs:/audio/phobos_room.mp3",true);
                }
            }

        } else if(mode==Mode::CutsceneMenu) {
            if(down&(KEY_B|KEY_START)) goMenu();
            if(down&KEY_UP) cutsceneIndex=(cutsceneIndex+CUTSCENE_COUNT-1)%CUTSCENE_COUNT;
            if(down&KEY_DOWN) cutsceneIndex=(cutsceneIndex+1)%CUTSCENE_COUNT;
            if(down&KEY_A) {
                if(cutsceneIndex==0) {
                    rerollIntro(intro,uiRng);
                    mode=Mode::Intro;
                    setMusic("romfs:/audio/intro.mp3",false);
                } else if(cutsceneIndex==1) {
                    startCutscene(CutsceneKind::Lines100,Mode::CutsceneMenu);
                } else if(cutsceneIndex==2) {
                    startCutscene(CutsceneKind::Lines200,Mode::CutsceneMenu);
                } else {
                    startCutscene(CutsceneKind::Ending,Mode::CutsceneMenu);
                }
            }

        } else if(mode==Mode::Cutscene) {
            const float elapsed=static_cast<float>(osGetTime()-cutscene.startedMs)/1000.0f;

            if(cutscene.kind==CutsceneKind::Ending) {
                if(down&(KEY_B|KEY_START)) {
                    mode=cutscene.returnMode;
                    if(mode==Mode::CutsceneMenu) setMusic("romfs:/audio/menu_1.mp3",true);
                    else if(mode==Mode::Tetris) startGameplayMusic(true);
                } else if(elapsed>=30.65f && ((down&KEY_A)||touchPressed)) {
                    mode=cutscene.returnMode;
                    if(mode==Mode::CutsceneMenu) setMusic("romfs:/audio/menu_1.mp3",true);
                    else if(mode==Mode::Tetris) startGameplayMusic(true);
                }
            } else {
                const int total=cutscene.kind==CutsceneKind::Lines100?8:6;
                const bool leave=(down&(KEY_B|KEY_START))!=0;
                const bool advance=((down&KEY_A)||touchPressed);
                if(leave || advance) {
                    if(advance) ++cutscene.frame;
                    if(leave || cutscene.frame>=total) {
                        if(cutscene.kind==CutsceneKind::Lines200 &&
                           cutscene.returnMode==Mode::Tetris) {
                            mode=Mode::RouteChoice;
                            routeChoice=0;
                            audio.play("romfs:/audio/music_winner_choice.mp3",true);
                        } else {
                            mode=cutscene.returnMode;
                            if(mode==Mode::Tetris) startGameplayMusic(true);
                            else if(mode==Mode::CutsceneMenu)
                                setMusic("romfs:/audio/menu_1.mp3",true);
                        }
                    }
                }
            }

        } else if(mode==Mode::RouteChoice) {
            if(down&(KEY_LEFT|KEY_RIGHT)) routeChoice=1-routeChoice;
            if(down&KEY_A) {
                guardiansRoute=(routeChoice==0);
                phobosRoute=(routeChoice==1);
                shown300=false;
                manualMusicPhase=-999;
                mode=Mode::Tetris;
                startGameplayMusic(true);
                codeMessage(guardiansRoute?"GUARDIANS ROUTE":"PHOBOS ROUTE");
            }

        } else if(mode==Mode::PhobosRoom) {
            if(down&(KEY_B|KEY_START)) goMenu();
            else if((down&(KEY_A|KEY_X)) || touchPressed) phobosState=(phobosState+1)%6;
        }

        C2D_TextBufClear(g_textBuf);
        C3D_FrameBegin(C3D_FRAME_SYNCDRAW);

        const float slider=osGet3DSliderState();
        auto renderScene=[&](C3D_RenderTarget* topTarget,float eye){
            const float endingElapsed=
                (mode==Mode::Cutscene && cutscene.kind==CutsceneKind::Ending)
                ? static_cast<float>(osGetTime()-cutscene.startedMs)/1000.0f : 0.0f;

            if(mode==Mode::Intro) renderIntro(topTarget,bottom,intro,eye);
            else if(mode==Mode::Menu) renderMenu(topTarget,bottom,menuIndex,audio,eye);
            else if(mode==Mode::Settings) renderSettings(topTarget,bottom,game,settingsPage,settingsIndex,eye);
            else if(mode==Mode::Tetris) {
                renderTetrisTop(game,topTarget,codes,guardiansRoute,phobosRoute,eye);
                renderTetrisBottom(game,bottom,audio,codes,guardiansRoute,phobosRoute);
            }
            else if(mode==Mode::CutsceneMenu) renderCutsceneMenu(topTarget,bottom,cutsceneIndex);
            else if(mode==Mode::Cutscene) renderCutscene(topTarget,bottom,cutscene,endingElapsed,eye);
            else if(mode==Mode::RouteChoice) renderRouteChoice(topTarget,bottom,routeChoice,eye);
            else renderPhobosRoom(topTarget,bottom,phobosState,eye);
        };

        renderScene(topLeft,-slider);
        if(slider>0.01f)
            renderScene(topRight,slider);

        C3D_FrameEnd(0);
    }

    voiceAudio.shutdown();
    audio.shutdown();
    g_assets.unloadAll();
    C2D_TextBufDelete(g_textBuf);
    C2D_Fini();
    C3D_Fini();
    romfsExit();
    gfxExit();
    return 0;
}
