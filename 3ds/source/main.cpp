#include <3ds.h>
#include <citro2d.h>

#include "audio_player.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <map>
#include <random>
#include <string>
#include <vector>

namespace {

constexpr int BOARD_W = 10;
constexpr int BOARD_H = 20;
constexpr int CELL = 11;
constexpr float BOARD_X = 145.0f;
constexpr float BOARD_Y = 10.0f;
constexpr int LOCK_DELAY_FRAMES = 30;
constexpr int SOFT_DROP_FRAMES = 2;
constexpr int FPS = 60;

struct Point { int x; int y; };

enum PieceKind : int { I = 0, O, T, S, Z, J, L, PIECE_COUNT };

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
    Game() : rng_(static_cast<unsigned int>(osGetTime())) { reset(); }

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
        pieceSerial_ = 0;
        lastSeen_.fill(0);
        nextKind_ = randomPiece();
        spawnPiece();
    }

    void togglePause() { if (!gameOver_) paused_ = !paused_; }
    bool paused() const { return paused_; }
    bool gameOver() const { return gameOver_; }
    int score() const { return score_; }
    int lines() const { return lines_; }
    int holdKind() const { return holdKind_; }
    int nextKind() const { return nextKind_; }
    int speedFrames() const { return gravityInterval(); }
    const Piece& current() const { return current_; }
    const std::array<std::array<int, BOARD_W>, BOARD_H>& board() const { return board_; }

    void developerAddLines(int amount = 10) {
        lines_ = std::max(0, lines_ + amount);
    }

    void developerClearBoard() {
        for (auto& row : board_) row.fill(-1);
        groundedFrames_ = 0;
        gravityFrames_ = 0;
    }

    void tick(bool softDropHeld) {
        if (paused_ || gameOver_) return;
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
        if (paused_ || gameOver_) return false;
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
        if (paused_ || gameOver_) return false;
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
        if (paused_ || gameOver_) return;
        int cells = 0;
        while (move(0, 1)) ++cells;
        score_ += cells * 2;
        lockPiece();
    }

    void hold() {
        if (paused_ || gameOver_ || holdUsed_) return;
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

    std::mt19937 rng_;
    std::vector<int> history_;
    std::array<int, PIECE_COUNT> lastSeen_{};
    int pieceSerial_ = 0;

    int gravityInterval() const {
        const int level = lines_ / 10;
        return std::max(4, 48 - level * 4);
    }

    int randomPiece() {
        std::array<float, PIECE_COUNT> weights{};
        float total = 0.0f;
        const int recent = history_.empty() ? -1 : history_.back();
        const bool triple = history_.size() >= 3 &&
            history_[history_.size()-1] == history_[history_.size()-2] &&
            history_[history_.size()-2] == history_[history_.size()-3];

        for (int k = 0; k < PIECE_COUNT; ++k) {
            if (triple && k == recent) {
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

        std::uniform_real_distribution<float> dist(0.0f, total);
        float pick = dist(rng_);
        for (int k = 0; k < PIECE_COUNT; ++k) {
            pick -= weights[k];
            if (pick <= 0.0f && weights[k] > 0.0f) return k;
        }
        return L;
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
            // Encoded cell = exact sprite fragment in phase1_cells.t3x.
            // kind * 16 + rotation * 4 + source-fragment slot.
            if (by >= 0 && by < BOARD_H && bx >= 0 && bx < BOARD_W)
                board_[by][bx] = current_.kind * 16 + current_.rot * 4 + slot;
        }
        clearLines();
        if (!gameOver_) spawnPiece();
    }

    void clearLines() {
        int cleared = 0;
        for (int y = BOARD_H - 1; y >= 0; --y) {
            bool full = true;
            for (int x = 0; x < BOARD_W; ++x) {
                if (board_[y][x] < 0) { full = false; break; }
            }
            if (!full) continue;
            ++cleared;
            for (int pull = y; pull > 0; --pull) board_[pull] = board_[pull - 1];
            board_[0].fill(-1);
            ++y;
        }
        static constexpr int SCORE_TABLE[5] = {0, 100, 300, 500, 800};
        lines_ += cleared;
        score_ += SCORE_TABLE[std::min(cleared, 4)];
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

void drawFragment(int encoded, float x, float y, float size = CELL, float depth = 0.54f) {
    const int kind = std::max(0, std::min(PIECE_COUNT - 1, encoded / 16));
    if (g_assets.has("cells")) {
        C2D_Image img = g_assets.image("cells", encoded);
        const float s = size / 24.0f;
        C2D_DrawImageAt(img, x, y, depth, nullptr, s, s);
    } else {
        C2D_DrawRectSolid(x, y, depth, size - 1, size - 1, PIECE_COLORS[kind]);
    }
}

void drawPieceAt(const Piece& piece, int yOverride, bool ghost = false) {
    for (int slot = 0; slot < 4; ++slot) {
        const Point& p = SHAPES[piece.kind][piece.rot][slot];
        const int gx = piece.x + p.x;
        const int gy = yOverride + p.y;
        if (gy < 0) continue;
        const float x = BOARD_X + gx * CELL;
        const float y = BOARD_Y + gy * CELL;
        if (ghost) {
            C2D_DrawRectSolid(x + 2, y + 2, 0.49f, CELL - 4, CELL - 4, color(210,150,255,85));
        } else {
            drawFragment(piece.kind * 16 + piece.rot * 4 + slot, x, y);
        }
    }
}

void drawMiniPiece(int kind, float x, float y, float cell = 8.0f) {
    for (int slot = 0; slot < 4; ++slot) {
        const Point& p = SHAPES[kind][0][slot];
        const float px = x + p.x * cell;
        const float py = y + p.y * cell;
        C2D_DrawRectSolid(px, py, 0.82f, cell - 1.0f, cell - 1.0f, PIECE_COLORS[kind]);
        C2D_DrawRectSolid(px + 1.0f, py + 1.0f, 0.83f, cell - 3.0f, 1.0f, color(255,255,255,80));
    }
}

void drawCharacterMiniPiece(int kind, float x, float y, float cell = 11.0f, float depth = 0.82f) {
    for (int slot = 0; slot < 4; ++slot) {
        const Point& p = SHAPES[kind][0][slot];
        const int encoded = kind * 16 + slot;
        drawFragment(encoded, x + p.x * cell, y + p.y * cell, cell, depth);
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


std::string phaseBackground(int lines) {
    if (lines >= 200) return "bg_phase2";
    if (lines >= 100) return "bg_phase1";
    return "bg_phase0";
}

void renderTetrisTop(const Game& game, C3D_RenderTarget* target,
                    const CodeKeyboardState& codes, float eyeShift = 0.0f) {
    const u32 text = color(245, 240, 250);
    const u32 accent = color(209, 143, 255);
    const u32 grid = color(102, 88, 118, 105);

    C2D_TargetClear(target, color(9, 7, 15));
    C2D_SceneBegin(target);
    drawFullscreenAsset(phaseBackground(game.lines()));
    C2D_DrawRectSolid(0, 0, 0.20f, 400, 240, color(0,0,0,28));

    drawPanel(5, 5, 128, 230, accent, 0.28f);
    drawPanel(140, 5, 120, 230, accent, 0.28f);
    drawPanel(267, 5, 128, 230, accent, 0.28f);

    C2D_DrawRectSolid(BOARD_X, BOARD_Y, 0.45f, BOARD_W * CELL, BOARD_H * CELL,
                      color(8,8,15,188));
    for (int x = 1; x < BOARD_W; ++x)
        C2D_DrawRectSolid(BOARD_X + x * CELL, BOARD_Y, 0.46f, 1, BOARD_H * CELL, grid);
    for (int y = 1; y < BOARD_H; ++y)
        C2D_DrawRectSolid(BOARD_X, BOARD_Y + y * CELL, 0.46f, BOARD_W * CELL, 1, grid);

    const auto& board = game.board();
    for (int y = 0; y < BOARD_H; ++y) {
        for (int x = 0; x < BOARD_W; ++x) {
            if (board[y][x] >= 0)
                drawFragment(board[y][x], BOARD_X + x * CELL, BOARD_Y + y * CELL);
        }
    }

    if (!game.gameOver()) {
        drawPieceAt(game.current(), game.ghostY(), true);
        drawPieceAt(game.current(), game.current().y, false);
    }

    char buf[96];
    drawText("W.I.T.C.H.", 15, 14, 0.55f, accent);
    drawText("TETRIS", 15, 37, 0.47f, text);
    std::snprintf(buf, sizeof(buf), "LINES %d", game.lines());
    drawText(buf, 15, 66, 0.36f, text);
    std::snprintf(buf, sizeof(buf), "SCORE %d", game.score());
    drawText(buf, 15, 85, 0.36f, text);
    std::snprintf(buf, sizeof(buf), "SPEED %df", game.speedFrames());
    drawText(buf, 15, 104, 0.36f, text);

    const char* phase = game.lines() >= 200 ? "GUARDIANS" :
                        (game.lines() >= 100 ? "RESISTANCE" : "PHOBOS");
    drawText(phase, 15, 124, 0.31f, accent);

    // Phobos keeps a visible place on the top screen, just like in the desktop
    // composition.  The eye-dependent offset gives him real stereoscopic depth.
    const std::string phobosKey = game.lines() >= 100 ? "phobos_resistance" : "phobos_gameplay";
    drawAssetFit(phobosKey, 18 + eyeShift * 5.0f, 133, 108, 96, 0.61f, false, 0.96f);

    drawText("NEXT", 279, 16, 0.38f, accent);
    drawCharacterMiniPiece(game.nextKind(), 306, 43, 13.0f, 0.82f);
    drawText(PIECE_CHARACTERS[game.nextKind()], 278, 88, 0.27f, text);

    drawText("HOLD", 279, 112, 0.38f, accent);
    if (game.holdKind() >= 0) {
        drawCharacterMiniPiece(game.holdKind(), 306, 139, 12.0f, 0.82f);
        drawText(PIECE_CHARACTERS[game.holdKind()], 278, 184, 0.27f, text);
    }
    drawText("START: MENU", 279, 211, 0.27f, text);

    if (codes.matrixFrames > 0) {
        C2D_DrawRectSolid(0,0,0.88f,400,240,color(0,90,20,70));
        drawText("MATRIX", 294, 219, 0.32f, color(90,255,120));
    }
    if (codes.jetixFrames > 0) {
        drawPanel(285, 192, 105, 37, color(255,180,60), 0.88f);
        drawText("JETIX", 307, 202, 0.45f, color(255,220,90));
    }

    if (game.paused()) {
        drawPanel(92, 78, 216, 82, accent, 0.90f);
        drawText("PAUSED", 146, 96, 0.66f, accent);
        drawText("SELECT: resume", 125, 128, 0.40f, text);
    } else if (game.gameOver()) {
        drawPanel(78, 72, 244, 98, color(225,75,95), 0.90f);
        drawText("GAME OVER", 120, 92, 0.66f, color(245,100,115));
        drawText("A: restart", 145, 126, 0.42f, text);
        drawText("START: menu", 137, 147, 0.36f, text);
    }
}

void renderTetrisBottom(const Game& game, C3D_RenderTarget* target,
                        const Mp3Player& audio, const CodeKeyboardState& codes) {
    if (codes.open) {
        renderCodeKeyboard(target, codes);
        return;
    }

    const u32 text = color(238, 234, 246);
    const u32 accent = color(205, 140, 255);

    C2D_TargetClear(target, color(12, 9, 20));
    C2D_SceneBegin(target);

    drawAssetFit(phaseBackground(game.lines()), 0, 0, 320, 240, 0.05f, true, 1.0f);
    C2D_DrawRectSolid(0, 0, 0.20f, 320, 240, color(0,0,0,62));

    drawPanel(7, 7, 172, 226, accent, 0.28f);
    drawText("CONTROLS", 16, 15, 0.39f, accent);
    drawText("D-PAD  MOVE / DROP", 16, 43, 0.29f, text);
    drawText("A / B  ROTATE", 16, 61, 0.29f, text);
    drawText("X      HOLD", 16, 79, 0.29f, text);
    drawText("Y / UP HARD DROP", 16, 97, 0.29f, text);
    drawText("SELECT PAUSE", 16, 115, 0.29f, text);
    drawText("START  MENU", 16, 133, 0.29f, text);

    drawText("AUDIO", 16, 157, 0.29f, accent);
    std::string status = audio.status();
    const bool audioError = status.find("FAIL") != std::string::npos;
    const u32 audioColor = audioError ? color(245,105,115) : text;
    drawText(status.substr(0, 23), 16, 176, 0.23f, audioColor);
    if (status.size() > 23)
        drawText(status.substr(23, 23), 16, 191, 0.23f, audioColor);

    C2D_DrawRectSolid(13, 208, 0.70f, 152, 22, color(92,47,123,235));
    drawText("TOUCH: CODE KEYBOARD", 23, 214, 0.27f, color(250,240,255));

    const std::string phobosKey = game.lines() >= 100 ? "phobos_resistance" : "phobos_gameplay";
    drawAssetFit(phobosKey, 174, 4, 142, 226, 0.58f, false, 1.0f);
    drawText("PHOBOS", 244, 211, 0.29f, accent);

    if (codes.messageFrames > 0 && !codes.message.empty()) {
        drawPanel(179, 8, 136, 37, accent, 0.84f);
        drawText(codes.message.substr(0, 22), 187, 20, 0.24f, text);
    }
}

enum class Mode {
    Intro,
    Menu,
    Tetris,
    CutsceneMenu,
    Cutscene,
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
    CutsceneKind kind = CutsceneKind::Lines100;
    int frame = 0;
    Mode returnMode = Mode::CutsceneMenu;
};

const char* MENU_ITEMS[] = {
    "NEW GAME",
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

void renderMenu(C3D_RenderTarget* top, C3D_RenderTarget* bottom, int selected, const Mp3Player& audio) {
    const u32 accent = color(211,143,255);
    const u32 text = color(245,240,250);

    C2D_TargetClear(top, color(8,7,14));
    C2D_SceneBegin(top);
    drawFullscreenAsset("bg_menu");
    C2D_DrawRectSolid(0, 0, 0.2f, 400, 240, color(0,0,0,75));
    if (g_assets.has("phobos_menu_body"))
        drawAssetFit("phobos_menu_body", 228, 20, 165, 212, 0.32f, false, 0.92f);
    drawPanel(13, 12, 220, 215, accent);
    drawText("W.I.T.C.H.", 28, 26, 0.72f, accent);
    drawText("TETRIS", 28, 52, 0.62f, text);
    drawText("NINTENDO 3DS", 28, 75, 0.34f, accent);

    for (int i = 0; i < MENU_COUNT; ++i) {
        const float y = 105 + i * 22;
        if (i == selected) C2D_DrawRectSolid(24, y-3, 0.8f, 190, 19, color(105,53,135,220));
        drawText(std::string(i == selected ? "> " : "  ") + MENU_ITEMS[i], 29, y, 0.40f, text);
    }

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
        drawText("Send me this red line if there is no sound.", 12, 177, 0.29f, color(245,170,180));

    drawText("D-Pad: select    A: open    START: exit", 12, 207, 0.36f, accent);
}

void renderIntro(C3D_RenderTarget* top, C3D_RenderTarget* bottom, const IntroState& intro) {
    const u32 accent = color(215,145,255);
    const u32 text = color(245,240,250);
    const int scene = intro.scene;

    C2D_TargetClear(top, color(3,3,8));
    C2D_SceneBegin(top);

    if (scene == 0) {
        drawFullscreenAsset("intro_castle");
        C2D_DrawRectSolid(0, 0, 0.30f, 400, 240, color(0,0,0,42));
        drawPanel(36, 162, 328, 58, accent, 0.80f);
        drawText("MERIDIAN — PHOBOS CASTLE", 72, 178, 0.42f, text);
    } else {
        drawFullscreenAsset("intro_throne");
        C2D_DrawRectSolid(0, 0, 0.25f, 400, 240, color(0,0,0,28));

        if (scene == 1) {
            drawAssetFit("intro_will", 30, 48, 135, 172, 0.46f);
            drawAssetFit("intro_phobos", 248, 24, 145, 200, 0.45f);
            drawPanel(48, 176, 304, 48, accent, 0.80f);
            drawText("WILL: IT'S OVER, PHOBOS!", 75, 191, 0.41f, text);
        } else if (scene == 2) {
            const std::string key = std::string("intro_") + INTRO_ASSET_KEYS[intro.secondKind];
            drawAssetFit(key, 120, 24, 160, 197, 0.49f);
            drawPanel(48, 176, 304, 48, accent, 0.80f);
            drawText(std::string(PIECE_CHARACTERS[intro.secondKind]) + ": WE WON'T SURRENDER!",
                     63, 191, 0.34f, text);
        } else if (scene == 3) {
            const bool casting = intro.frames > 95;
            drawAssetFit(casting ? "intro_phobos_cast" : "intro_phobos",
                         100, 16, 200, 207, 0.49f);
            drawPanel(42, 176, 316, 48, accent, 0.80f);
            drawText("PHOBOS: EVERYTHING IS JUST BEGINNING.", 55, 191, 0.33f, text);
        } else if (scene == 4) {
            drawAssetFit("intro_phobos_cast", 90, 10, 220, 216, 0.55f);
            const int pulse = (intro.frames / 8) % 2;
            if (pulse)
                C2D_DrawRectSolid(0,0,0.73f,400,240,color(220,175,255,52));
            drawText("THE SPELL", 150, 202, 0.40f, accent);
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
                    drawAssetFit(key, xs[kind], 64 + (kind%2)*10, 52, 142, 0.56f);
                }
                drawPanel(43, 187, 314, 38, accent, 0.81f);
                drawText("ALL SEVEN ARE TRANSFORMING", 78, 198, 0.34f, text);
            } else {
                std::string key;
                if (intro.transformKind == Z && intro.horrorIrma && stage == 2) {
                    // Z is Will in gameplay. Horror Irma is only valid when Irma
                    // itself is selected, so this branch is intentionally not used.
                    key = introAssetKey(intro.transformKind, stageName);
                } else if (intro.transformKind == S && intro.horrorIrma && stage == 2) {
                    key = "intro_irma_horror";
                } else {
                    key = introAssetKey(intro.transformKind, stageName);
                }
                drawAssetFit(key, 115, 16, 170, 205, 0.57f);
                drawPanel(48, 177, 304, 47, accent, 0.82f);
                drawText(std::string(PIECE_CHARACTERS[intro.transformKind]) + " — TRANSFORMATION",
                         78, 191, 0.35f, text);
            }
        } else if (scene == 6) {
            drawAssetFit("intro_phobos", 104, 14, 192, 210, 0.50f);
            drawPanel(48, 177, 304, 47, accent, 0.82f);
            drawText("PHOBOS: NOW YOUR POWER IS MINE.", 67, 191, 0.34f, text);
        } else {
            drawFullscreenAsset("bg_phase0");
            C2D_DrawRectSolid(0,0,0.32f,400,240,color(0,0,0,105));
            drawPanel(52, 72, 296, 100, accent, 0.80f);
            drawText("W.I.T.C.H. TETRIS", 92, 93, 0.70f, accent);
            drawText("THE GAME HAS BEGUN.", 104, 132, 0.41f, text);
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

void renderCutscene(C3D_RenderTarget* top, C3D_RenderTarget* bottom, const CutsceneState& cs) {
    const u32 accent=color(211,143,255), text=color(245,240,250);
    C2D_TargetClear(top,color(4,3,8));
    C2D_SceneBegin(top);

    std::string title;
    int total=1;

    if(cs.kind==CutsceneKind::Lines100) {
        title="100 LINES — RESISTANCE";
        const char* frames[]={"l100_phobos","l100_will","l100_cornelia","l100_irma","l100_taranee","l100_haylin","l100_caleb","l100_heart"};
        total=8;
        drawFullscreenAsset("bg_phase1");
        C2D_DrawRectSolid(0,0,0.25f,400,240,color(0,0,0,75));
        drawAssetFit(frames[cs.frame%total],70,18,260,205,0.5f);
    } else if(cs.kind==CutsceneKind::Lines200) {
        title="200 LINES — PHOBOS COLLAPSES";
        total=6;
        drawFullscreenAsset("bg_phase2");
        C2D_DrawRectSolid(0,0,0.25f,400,240,color(0,0,0,75));
        char key[32];
        std::snprintf(key,sizeof(key),"l200_collapse_%d",cs.frame%6);
        drawAssetFit(key,40,10,320,220,0.5f);
    } else {
        title="ENDING — W.I.T.C.H.";
        total=2;
        drawFullscreenAsset(cs.frame%2==0?"ending_phobos":"ending_witch",0.12f);
        C2D_DrawRectSolid(0,0,0.25f,400,240,color(0,0,0,20));
    }
    drawPanel(8,5,384,29,accent,0.80f);
    drawText(title,20,12,0.38f,text);

    C2D_TargetClear(bottom,color(12,9,20));
    C2D_SceneBegin(bottom);
    drawText(title,12,16,0.47f,accent);
    char buf[64];
    std::snprintf(buf,sizeof(buf),"FRAME %d / %d",cs.frame+1,total);
    drawText(buf,12,62,0.40f,text);
    C2D_DrawRectSolid(12,112,0.75f,296,50,color(88,45,118,230));
    drawText("A / TOUCH — NEXT",67,128,0.46f,text);
    drawText("B / START — leave scene",12,174,0.40f,text);
    drawText("Original artwork, scaled for 400x240.",12,210,0.34f,accent);
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

void renderPhobosRoom(C3D_RenderTarget* top,C3D_RenderTarget* bottom,int state) {
    const u32 accent=color(210,140,255),text=color(245,240,250);
    C2D_TargetClear(top,color(5,3,8));
    C2D_SceneBegin(top);
    drawFullscreenAsset("phobos_room_bg");
    char key[32];
    std::snprintf(key,sizeof(key),"phobos_room_state%d",state%6);
    drawAssetFit(key,103,25,194,190,0.52f);
    drawAssetFit("phobos_room_table",0,142,400,98,0.70f,true);
    drawPanel(15,12,190,42,accent,0.80f);
    drawText("PHOBOS ROOM",28,24,0.47f,text);

    C2D_TargetClear(bottom,color(11,7,18));
    C2D_SceneBegin(bottom);
    drawText("PHOBOS ROOM — NATIVE 3DS TEST",12,15,0.45f,accent);
    drawText("Original layered room artwork is active.",12,58,0.37f,text);
    drawText("A / X — change seated state",12,103,0.42f,text);
    drawText("B / START — return to menu",12,132,0.42f,text);
    char buf[48]; std::snprintf(buf,sizeof(buf),"POSE %d / 6",state+1);
    drawText(buf,12,201,0.38f,accent);
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

std::string musicForTetris(int lines) {
    if(lines>=200) return "romfs:/audio/phase2_guardians.mp3";
    if(lines>=100) {
        const int which=(lines/10)%3;
        return std::string("romfs:/audio/phase1_")+char('1'+which)+".mp3";
    }
    return "romfs:/audio/phase0.mp3";
}

} // namespace

int main() {
    gfxInitDefault();
    romfsInit();
    C3D_Init(C3D_DEFAULT_CMDBUF_SIZE);
    C2D_Init(C2D_DEFAULT_MAX_OBJECTS);
    C2D_Prepare();

    initColors();
    initShapes();

    C3D_RenderTarget* top=C2D_CreateScreenTarget(GFX_TOP,GFX_LEFT);
    C3D_RenderTarget* bottom=C2D_CreateScreenTarget(GFX_BOTTOM,GFX_LEFT);
    g_textBuf=C2D_TextBufNew(8192);
    Mp3Player audio;
    audio.init();

    Game game;
    Mode mode=Mode::Intro;
    CutsceneState cutscene;
    int introScene=0;
    int menuIndex=0;
    int cutsceneIndex=0;
    int phobosState=0;
    int repeatDir=0,repeatTimer=0;
    bool shown100=false,shown200=false;
    bool quit=false;
    std::string wantedMusic;

    auto setMusic=[&](const std::string& path,bool loop=true){
        if(audio.ready() && audio.path()!=path) audio.play(path,loop);
    };
    auto goMenu=[&](){
        mode=Mode::Menu;
        menuIndex=0;
        setMusic((osGetTime()/1000)%2?"romfs:/audio/menu_1.mp3":"romfs:/audio/menu_2.mp3",true);
    };
    auto startCutscene=[&](CutsceneKind kind,Mode ret){
        cutscene.kind=kind;cutscene.frame=0;cutscene.returnMode=ret;mode=Mode::Cutscene;
        if(kind==CutsceneKind::Ending) setMusic("romfs:/audio/phase2_guardians.mp3",false);
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

        if(mode==Mode::Intro) {
            if(down&(KEY_B|KEY_START)) {
                goMenu();
            } else if((down&KEY_A)||touchPressed) {
                ++introScene;
                if(introScene>=6) goMenu();
            }
            setMusic("romfs:/audio/intro.mp3",false);
        } else if(mode==Mode::Menu) {
            if(down&KEY_START) quit=true;
            if(down&KEY_UP) menuIndex=(menuIndex+MENU_COUNT-1)%MENU_COUNT;
            if(down&KEY_DOWN) menuIndex=(menuIndex+1)%MENU_COUNT;
            if(down&KEY_A) {
                if(menuIndex==0) {
                    game.reset();shown100=false;shown200=false;mode=Mode::Tetris;
                    setMusic(musicForTetris(0),true);
                } else if(menuIndex==1) {
                    mode=Mode::CutsceneMenu;cutsceneIndex=0;
                } else if(menuIndex==2) {
                    mode=Mode::PhobosRoom;phobosState=0;
                    setMusic("romfs:/audio/phobos_room.mp3",true);
                } else quit=true;
            }
        } else if(mode==Mode::Tetris) {
            if(down&KEY_START) {
                goMenu();
            } else {
                if(down&KEY_SELECT) game.togglePause();
                if(game.gameOver()) {
                    if(down&KEY_A) {game.reset();shown100=false;shown200=false;setMusic(musicForTetris(0),true);}
                } else if(!game.paused()) {
                    handleHorizontalRepeat(game,down,held,repeatDir,repeatTimer);
                    if(down&KEY_A) game.rotate(+1);
                    if(down&KEY_B) game.rotate(-1);
                    if(down&KEY_X) game.hold();
                    if((down&KEY_UP)||(down&KEY_Y)) game.hardDrop();
                    game.tick((held&KEY_DOWN)!=0);
                }
                setMusic(musicForTetris(game.lines()),true);
                if(!shown100&&game.lines()>=100) {
                    shown100=true;startCutscene(CutsceneKind::Lines100,Mode::Tetris);
                } else if(!shown200&&game.lines()>=200) {
                    shown200=true;startCutscene(CutsceneKind::Lines200,Mode::Tetris);
                }
            }
        } else if(mode==Mode::CutsceneMenu) {
            if(down&(KEY_B|KEY_START)) goMenu();
            if(down&KEY_UP) cutsceneIndex=(cutsceneIndex+CUTSCENE_COUNT-1)%CUTSCENE_COUNT;
            if(down&KEY_DOWN) cutsceneIndex=(cutsceneIndex+1)%CUTSCENE_COUNT;
            if(down&KEY_A) {
                if(cutsceneIndex==0) {mode=Mode::Intro;introScene=0;setMusic("romfs:/audio/intro.mp3",false);}
                else if(cutsceneIndex==1) startCutscene(CutsceneKind::Lines100,Mode::CutsceneMenu);
                else if(cutsceneIndex==2) startCutscene(CutsceneKind::Lines200,Mode::CutsceneMenu);
                else startCutscene(CutsceneKind::Ending,Mode::CutsceneMenu);
            }
        } else if(mode==Mode::Cutscene) {
            int total=cutscene.kind==CutsceneKind::Lines100?8:(cutscene.kind==CutsceneKind::Lines200?6:2);
            if(down&(KEY_B|KEY_START)) {
                Mode ret=cutscene.returnMode;
                mode=ret;
                if(ret==Mode::Tetris) setMusic(musicForTetris(game.lines()),true);
                else if(ret==Mode::CutsceneMenu) setMusic("romfs:/audio/menu_1.mp3",true);
            } else if((down&KEY_A)||touchPressed) {
                ++cutscene.frame;
                if(cutscene.frame>=total) {
                    Mode ret=cutscene.returnMode;mode=ret;
                    if(ret==Mode::Tetris) setMusic(musicForTetris(game.lines()),true);
                    else setMusic("romfs:/audio/menu_1.mp3",true);
                }
            }
        } else if(mode==Mode::PhobosRoom) {
            if(down&(KEY_B|KEY_START)) goMenu();
            else if(down&(KEY_A|KEY_X)) phobosState=(phobosState+1)%6;
        }

        C2D_TextBufClear(g_textBuf);
        C3D_FrameBegin(C3D_FRAME_SYNCDRAW);

        if(mode==Mode::Intro) renderIntro(top,bottom,introScene);
        else if(mode==Mode::Menu) renderMenu(top,bottom,menuIndex,audio);
        else if(mode==Mode::Tetris) {renderTetrisTop(game,top);renderTetrisBottom(game,bottom,audio);}
        else if(mode==Mode::CutsceneMenu) renderCutsceneMenu(top,bottom,cutsceneIndex);
        else if(mode==Mode::Cutscene) renderCutscene(top,bottom,cutscene);
        else renderPhobosRoom(top,bottom,phobosState);

        C3D_FrameEnd(0);
    }

    audio.shutdown();
    g_assets.unloadAll();
    C2D_TextBufDelete(g_textBuf);
    C2D_Fini();
    C3D_Fini();
    romfsExit();
    gfxExit();
    return 0;
}
