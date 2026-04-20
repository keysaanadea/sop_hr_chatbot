#!/bin/bash
# ============================================================
# DENAI Launch Video — Audio Downloader
# Semua file gratis dari Mixkit (no attribution required)
# ============================================================

PUBLIC="./public"
mkdir -p "$PUBLIC"

echo ""
echo "📥 Downloading SFX dari Mixkit..."
echo ""

# 1. Whoosh — scene transitions
echo "  → sfx-whoosh.mp3"
curl -L -o "$PUBLIC/sfx-whoosh.mp3" \
  "https://assets.mixkit.co/active_storage/sfx/2571/2571-preview.mp3"

# 2. Boom — DENAI logo reveal impact
echo "  → sfx-boom.mp3"
curl -L -o "$PUBLIC/sfx-boom.mp3" \
  "https://assets.mixkit.co/active_storage/sfx/1470/1470-preview.mp3"

# 3. Typing — search input animation
echo "  → sfx-typing.mp3"
curl -L -o "$PUBLIC/sfx-typing.mp3" \
  "https://assets.mixkit.co/active_storage/sfx/2701/2701-preview.mp3"

# 4. Ping — chat message notification
echo "  → sfx-ping.mp3"
curl -L -o "$PUBLIC/sfx-ping.mp3" \
  "https://assets.mixkit.co/active_storage/sfx/1990/1990-preview.mp3"

# 5. Mic pop — call mode start
echo "  → sfx-mic.mp3"
curl -L -o "$PUBLIC/sfx-mic.mp3" \
  "https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3"

echo ""
echo "✅ SFX selesai didownload!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎵 BACKGROUND MUSIC — Download manual:"
echo ""
echo "  Rekomendasi terbaik (gratis, no attribution):"
echo ""
echo "  OPSI 1 — Pixabay (download langsung):"
echo "  https://pixabay.com/music/search/corporate%20inspiring/"
echo "  Cari: 'Corporate Inspiring' atau 'Epic Product Launch'"
echo "  Simpan sebagai: public/music.mp3"
echo ""
echo "  OPSI 2 — Mixkit:"
echo "  https://mixkit.co/free-stock-music/corporate/"
echo "  Cari: 'Inspiring corporate' atau 'Upbeat corporate'"
echo "  Simpan sebagai: public/music.mp3"
echo ""
echo "  OPSI 3 — YouTube Audio Library (gratis):"
echo "  https://studio.youtube.com/channel/music"
echo "  Filter: Genre=Corporate, Mood=Inspiring"
echo "  Simpan sebagai: public/music.mp3"
echo ""
echo "  Setelah download, taruh di:"
echo "  launch-video/public/music.mp3"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
