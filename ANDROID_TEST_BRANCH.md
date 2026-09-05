# Android TEST branch — based on desktop v6.17

This folder is a disposable phone-testing branch. It is **not** the next desktop development version.
All future normal development should continue from the original desktop **v6.17** archive unless explicitly requested otherwise.

## Touch controls

Bottom row: LEFT, RIGHT, ROTATE, DOWN (hold for soft drop), HOLD/RESERVE.
Upper utility row: PAUSE and +10 TEST.

LEFT/RIGHT support hold-repeat. ROTATE and HOLD fire once per press. +10 TEST calls the existing developer checkpoint helper, so it can be used to reach 100 and 200 lines quickly.

The game itself remains rendered at its original 860x1060 internal canvas. Android reserves a separate physical-screen strip below it for controls, so the desktop Tetris geometry is untouched.

## Important packaging note

pygame/pygame-ce is not currently an officially shipped upstream python-for-android recipe. This test bundle therefore includes an experimental local pygame-ce recipe derived from the open python-for-android pygame-ce recipe work. The Python source passes compile checks, but an actual Android NDK build cannot be executed in the current environment, so the APK step may expose toolchain-specific issues.
