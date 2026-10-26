# g3 — gradius3 だけを入れた MAME（Linux x86-64）

- MAME: 0.289 (unknown)（https://github.com/mamedev/mame のコミット 8dcfb5c90f3d3ae7845bdfee96c8f9eb09614842）
- ライセンス: MAME は GPL-2.0-or-later（一部 BSD-3-Clause）。ソースは上のリポジトリのそのコミット。
- 同梱: SDL2 / SDL2_ttf（zlib ライセンス, https://github.com/libsdl-org）
- 使い方: `./g3 gradius3 -rompath <ROMのフォルダ> ...`（ラッパーが同梱ライブラリと画面なしの設定をする）

## 自分でビルドする場合

```bash
# SDL2 と SDL2_ttf を /opt/sdl に入れる（GitHub の libsdl-org/SDL release-2.30.x, SDL_ttf release-2.22.x を cmake でビルド）
# GL/gl.h が無い環境では、SDL の SDL_opengl.h を include するだけの GL/gl.h と、
# mame/3rdparty/bgfx/3rdparty/khronos の EGL・KHR を /usr/local/include に置く
git clone --depth 1 https://github.com/mamedev/mame.git && cd mame
make SUBTARGET=g3 SOURCES=src/mame/konami/gradius3.cpp NOWERROR=1 NO_USE_MIDI=1 NO_X11=1 NO_USE_XINPUT=1 NO_OPENGL=1 \
  NO_USE_PORTAUDIO=1 NO_USE_PULSEAUDIO=1 NO_USE_PIPEWIRE=1 USE_QTDEBUG=0 OPTIMIZE=2 SYMBOLS=0 -j"$(nproc)"
```
