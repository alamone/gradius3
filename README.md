# mame-g3-bin

検証・開発用の MAME（gradius3 ドライバだけ、Linux x86-64、SDL 同梱）を置くための枝です。ゲームの改造パッチではありません。ROM は含まれていません。

```bash
git clone -q --depth 1 -b mame-g3-bin https://github.com/hknroms/gradius3.git g3pkg
tar xzf g3pkg/g3-linux-x64.tar.gz -C "$HOME"
export G3="$HOME/g3/g3"; "$G3" -version
```

ライセンスとビルド方法は BUILD.md（MAME は GPL-2.0-or-later、ソースは https://github.com/mamedev/mame ）。
