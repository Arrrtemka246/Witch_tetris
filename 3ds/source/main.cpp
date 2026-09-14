#include <3ds.h>
#include <citro2d.h>

#include <algorithm>
#include <array>
#include <cstdio>
#include <random>
#include <vector>

namespace {
constexpr int BOARD_W = 10;
constexpr int BOARD_H = 20;
constexpr int CELL = 10;
constexpr float BOARD_X = 112.0f;
constexpr float BOARD_Y = 20.0f;
constexpr int LOCK_DELAY_FRAMES = 30;
constexpr int SOFT_DROP_FRAMES = 2;

struct Point { int x; int y; };

enum PieceKind : int { I = 0, O, T, S, Z, J, L, PIECE_COUNT };

constexpr Point BASE_SHAPES[PIECE_COUNT][4] = {
    {{0,0},{0,1},{0,2},{0,3}}, // I
    {{0,0},{1,0},{0,1},{1,1}}, // O
    {{0,0},{1,0},{2,0},{1,1}}, // T
    {{0,0},{1,0},{1,1},{2,1}}, // S
    {{1,0},{2,0},{0,1},{1,1}}, // Z
    {{0,0},{0,1},{1,1},{2,1}}, // J
    {{2,0},{0,1},{1,1},{2,1}}, // L
};

const char* PIECE_NAMES[PIECE_COUNT] = {"I","O","T","S","Z","J","L"};

u32 PIECE_COLORS[PIECE_COUNT];
Point SHAPES[PIECE_COUNT][4][4];

u32 color(u8 r, u8 g, u8 b, u8 a = 0xFF) {
    return C2D_Color32(r, g, b, a);
}

void initColors() {
    PIECE_COLORS[I] = color(0, 210, 220);
    PIECE_COLORS[J] = color(20, 25, 235);
    PIECE_COLORS[L] = color(242, 158, 0);
    PIECE_COLORS[O] = color(242, 238, 0);
    PIECE_COLORS[S] = color(0, 225, 25);
    PIECE_COLORS[T] = color(165, 0, 235);
    PIECE_COLORS[Z] = color(238, 0, 0);
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

    void togglePause() {
        if (!gameOver_) paused_ = !paused_;
    }

    bool paused() const { return paused_; }
    bool gameOver() const { return gameOver_; }
    int score() const { return score_; }
    int lines() const { return lines_; }
    int holdKind() const { return holdKind_; }
    int nextKind() const { return nextKind_; }
    const Piece& current() const { return current_; }
    const std::array<std::array<int, BOARD_W>, BOARD_H>& board() const { return board_; }

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
        // Port of the default "Phobos" controlled-chaos selector in main.py:
        // drought protection, repeat penalty, and a hard stop after triples.
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
        for (const Point& p : SHAPES[current_.kind][current_.rot]) {
            const int bx = current_.x + p.x;
            const int by = current_.y + p.y;
            if (by >= 0 && by < BOARD_H && bx >= 0 && bx < BOARD_W) board_[by][bx] = current_.kind;
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
            ++y; // re-check this row after pulling
        }
        static constexpr int SCORE_TABLE[5] = {0, 100, 300, 500, 800};
        lines_ += cleared;
        score_ += SCORE_TABLE[std::min(cleared, 4)];
    }
};

C2D_TextBuf g_textBuf = nullptr;

void drawText(const char* str, float x, float y, float scale, u32 col) {
    C2D_Text text;
    C2D_TextParse(&text, g_textBuf, str);
    C2D_TextOptimize(&text);
    C2D_DrawText(&text, C2D_WithColor, x, y, 0.6f, scale, scale, col);
}

void drawCell(float x, float y, u32 col, bool ghost = false) {
    if (ghost) {
        C2D_DrawRectSolid(x + 1, y + 1, 0.25f, CELL - 2, CELL - 2, col);
        return;
    }
    C2D_DrawRectSolid(x, y, 0.3f, CELL - 1, CELL - 1, col);
    C2D_DrawRectSolid(x + 1, y + 1, 0.31f, CELL - 3, 2, color(255,255,255,70));
}

void drawPieceAt(const Piece& piece, int yOverride, bool ghost = false) {
    const u32 col = ghost ? color(178, 108, 255, 80) : PIECE_COLORS[piece.kind];
    for (const Point& p : SHAPES[piece.kind][piece.rot]) {
        const int gx = piece.x + p.x;
        const int gy = yOverride + p.y;
        if (gy < 0) continue;
        drawCell(BOARD_X + gx * CELL, BOARD_Y + gy * CELL, col, ghost);
    }
}

void drawMiniPiece(int kind, float x, float y) {
    for (const Point& p : SHAPES[kind][0]) {
        C2D_DrawRectSolid(x + p.x * 8.0f, y + p.y * 8.0f, 0.3f, 7.0f, 7.0f, PIECE_COLORS[kind]);
    }
}

void renderTop(const Game& game, C3D_RenderTarget* target) {
    const u32 bg = color(11, 11, 18);
    const u32 boardBg = color(18, 20, 30);
    const u32 grid = color(42, 44, 58);
    const u32 text = color(235, 235, 245);
    const u32 accent = color(178, 108, 255);

    C2D_TargetClear(target, bg);
    C2D_SceneBegin(target);

    C2D_DrawRectSolid(BOARD_X - 2, BOARD_Y - 2, 0.1f, BOARD_W * CELL + 4, BOARD_H * CELL + 4, accent);
    C2D_DrawRectSolid(BOARD_X, BOARD_Y, 0.2f, BOARD_W * CELL, BOARD_H * CELL, boardBg);

    for (int x = 1; x < BOARD_W; ++x)
        C2D_DrawRectSolid(BOARD_X + x * CELL, BOARD_Y, 0.21f, 1, BOARD_H * CELL, grid);
    for (int y = 1; y < BOARD_H; ++y)
        C2D_DrawRectSolid(BOARD_X, BOARD_Y + y * CELL, 0.21f, BOARD_W * CELL, 1, grid);

    const auto& board = game.board();
    for (int y = 0; y < BOARD_H; ++y)
        for (int x = 0; x < BOARD_W; ++x)
            if (board[y][x] >= 0)
                drawCell(BOARD_X + x * CELL, BOARD_Y + y * CELL, PIECE_COLORS[board[y][x]]);

    if (!game.gameOver()) {
        drawPieceAt(game.current(), game.ghostY(), true);
        drawPieceAt(game.current(), game.current().y, false);
    }

    char buf[64];
    drawText("W.I.T.C.H. TETRIS", 10, 8, 0.55f, accent);
    std::snprintf(buf, sizeof(buf), "SCORE  %d", game.score());
    drawText(buf, 10, 42, 0.48f, text);
    std::snprintf(buf, sizeof(buf), "LINES  %d", game.lines());
    drawText(buf, 10, 62, 0.48f, text);
    std::snprintf(buf, sizeof(buf), "LEVEL  %d", game.lines() / 10 + 1);
    drawText(buf, 10, 82, 0.48f, text);

    drawText("HOLD", 10, 118, 0.44f, text);
    if (game.holdKind() >= 0) drawMiniPiece(game.holdKind(), 22, 142);

    drawText("NEXT", 238, 28, 0.44f, text);
    drawMiniPiece(game.nextKind(), 250, 55);
    drawText("3DS native", 238, 118, 0.42f, accent);
    drawText("phase 1", 238, 136, 0.42f, text);

    if (game.paused()) {
        C2D_DrawRectSolid(82, 84, 0.8f, 236, 72, color(0,0,0,210));
        drawText("PAUSED", 151, 102, 0.8f, accent);
        drawText("SELECT to resume", 118, 132, 0.45f, text);
    } else if (game.gameOver()) {
        C2D_DrawRectSolid(70, 76, 0.8f, 260, 92, color(0,0,0,220));
        drawText("GAME OVER", 123, 94, 0.8f, color(220,80,95));
        drawText("A: restart", 146, 128, 0.48f, text);
        drawText("START: exit", 141, 147, 0.42f, text);
    }
}

void renderBottom(const Game& game, C3D_RenderTarget* target) {
    const u32 bg = color(16, 14, 24);
    const u32 text = color(230, 226, 240);
    const u32 accent = color(178, 108, 255);
    C2D_TargetClear(target, bg);
    C2D_SceneBegin(target);

    drawText("W.I.T.C.H. Tetris / Nintendo 3DS", 12, 12, 0.46f, accent);
    drawText("D-Pad L/R : move", 12, 50, 0.42f, text);
    drawText("D-Pad Down: soft drop", 12, 72, 0.42f, text);
    drawText("D-Pad Up/Y: hard drop", 12, 94, 0.42f, text);
    drawText("A/B       : rotate CW/CCW", 12, 116, 0.42f, text);
    drawText("X         : HOLD", 12, 138, 0.42f, text);
    drawText("SELECT    : pause", 12, 160, 0.42f, text);
    drawText("START     : exit to Homebrew Menu", 12, 182, 0.42f, text);

    char buf[80];
    std::snprintf(buf, sizeof(buf), "Current: %s   Next: %s", PIECE_NAMES[game.current().kind], PIECE_NAMES[game.nextKind()]);
    drawText(buf, 12, 214, 0.38f, game.gameOver() ? color(220,80,95) : text);
}

void handleHorizontalRepeat(Game& game, u32 down, u32 held, int& repeatDir, int& repeatTimer) {
    int dir = 0;
    if (held & KEY_LEFT) dir = -1;
    else if (held & KEY_RIGHT) dir = 1;

    if ((down & KEY_LEFT) || (down & KEY_RIGHT)) {
        repeatDir = dir;
        repeatTimer = 12;
        if (dir) game.move(dir, 0);
        return;
    }

    if (dir == 0) {
        repeatDir = 0;
        repeatTimer = 0;
        return;
    }
    if (dir != repeatDir) {
        repeatDir = dir;
        repeatTimer = 12;
        game.move(dir, 0);
        return;
    }
    if (repeatTimer > 0) {
        --repeatTimer;
    } else {
        game.move(dir, 0);
        repeatTimer = 3;
    }
}

} // namespace

int main() {
    gfxInitDefault();
    C3D_Init(C3D_DEFAULT_CMDBUF_SIZE);
    C2D_Init(C2D_DEFAULT_MAX_OBJECTS);
    C2D_Prepare();

    initColors();
    initShapes();

    C3D_RenderTarget* top = C2D_CreateScreenTarget(GFX_TOP, GFX_LEFT);
    C3D_RenderTarget* bottom = C2D_CreateScreenTarget(GFX_BOTTOM, GFX_LEFT);
    g_textBuf = C2D_TextBufNew(4096);

    Game game;
    int repeatDir = 0;
    int repeatTimer = 0;

    while (aptMainLoop()) {
        hidScanInput();
        const u32 down = hidKeysDown();
        const u32 held = hidKeysHeld();

        if (down & KEY_START) break;
        if (down & KEY_SELECT) game.togglePause();

        if (game.gameOver()) {
            if (down & KEY_A) game.reset();
        } else if (!game.paused()) {
            handleHorizontalRepeat(game, down, held, repeatDir, repeatTimer);
            if (down & KEY_A) game.rotate(+1);
            if (down & KEY_B) game.rotate(-1);
            if (down & KEY_X) game.hold();
            if ((down & KEY_UP) || (down & KEY_Y)) game.hardDrop();
            game.tick((held & KEY_DOWN) != 0);
        }

        C2D_TextBufClear(g_textBuf);
        C3D_FrameBegin(C3D_FRAME_SYNCDRAW);
        renderTop(game, top);
        renderBottom(game, bottom);
        C3D_FrameEnd(0);
    }

    C2D_TextBufDelete(g_textBuf);
    C2D_Fini();
    C3D_Fini();
    gfxExit();
    return 0;
}
