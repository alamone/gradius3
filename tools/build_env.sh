#!/bin/bash
# Gradius III 解析環境の構築（Ubuntu 24.04 / apt不可・GitHubのgit cloneのみ可の環境で動作確認済み）
# 所要時間: SDL数分 + MAME(グラディウスIIIドライバのみ) 約30〜40分（2コア）
set -e
B=${B:-$HOME/build}
mkdir -p $B && cd $B

# 1) SDL2 / SDL2_ttf をソースからビルド（/opt/sdl へ）
git clone -q --depth 1 -b release-2.30.9 https://github.com/libsdl-org/SDL.git sdl
git clone -q --depth 1 -b release-2.22.0 https://github.com/libsdl-org/SDL_ttf.git sdlttf
(mkdir -p sdl/b && cd sdl/b && cmake .. -DCMAKE_INSTALL_PREFIX=/opt/sdl -DCMAKE_BUILD_TYPE=Release -DSDL_TEST=OFF >/dev/null && make -j2 >/dev/null && make install >/dev/null)
(mkdir -p sdlttf/b && cd sdlttf/b && cmake .. -DCMAKE_INSTALL_PREFIX=/opt/sdl -DCMAKE_PREFIX_PATH=/opt/sdl -DSDL2TTF_VENDORED=OFF -DSDL2TTF_HARFBUZZ=OFF -DSDL2TTF_SAMPLES=OFF >/dev/null && make -j2 >/dev/null && make install >/dev/null)
# libEGL.so / libGL.so の開発用シンボリックリンクが無い環境向け
ln -sf /usr/lib/x86_64-linux-gnu/libEGL.so.1 /opt/sdl/lib/libEGL.so
ln -sf /usr/lib/x86_64-linux-gnu/libGL.so.1  /opt/sdl/lib/libGL.so

# 2) MAME（gradius3ドライバだけの小さなバイナリ "g3"）
git clone -q --depth 1 -b mame0270 https://github.com/mamedev/mame.git mame
cd mame
export PATH=/opt/sdl/bin:$PATH PKG_CONFIG_PATH=/opt/sdl/lib/pkgconfig
make -j2 SUBTARGET=g3 SOURCES=src/mame/konami/gradius3.cpp \
  NO_X11=1 NO_OPENGL=1 NO_USE_XINPUT=1 NO_USE_PORTAUDIO=1 NO_USE_PULSEAUDIO=1 \
  NO_USE_PIPEWIRE=1 NO_USE_MIDI=1 USE_QTDEBUG=0 TOOLS=0 TESTS=0 OPTIMIZE=2 SYMLEVEL=0 \
  ARCHOPTS="-L/opt/sdl/lib" LDOPTS="-L/opt/sdl/lib"
ls -la g3

# 3) 68000逆アセンブラ capstone（Pythonバインディングはソースのまま使う）
cd $B
git clone -q --depth 1 -b 5.0.3 https://github.com/capstone-engine/capstone.git cs
(mkdir -p cs/b && cd cs/b && cmake .. -DCMAKE_BUILD_TYPE=Release -DCAPSTONE_ARCHITECTURE_DEFAULT=OFF -DCAPSTONE_M68K_SUPPORT=ON -DBUILD_SHARED_LIBS=ON -DCMAKE_INSTALL_PREFIX=/opt/cs >/dev/null && make -j2 >/dev/null && make install >/dev/null)
echo "done. capstone python binding: $B/cs/bindings/python  (LIBCAPSTONE_PATH=/opt/cs/lib)"
