# Letter Trucks — notes for Claude

A truck game in the browser that teaches a toddler (almost 3) lowercase letters and letter sounds. He already knows the uppercase letter names. The owner is his mom. She doesn't code, so Claude does all of the code, building and testing.

**How she likes to work:** lowercase, chill, not overly enthusiastic. Challenge weak assumptions, and say clearly what's fact, what's inference and what's speculation. Ask when something is genuinely unclear. Keep summaries short.

**Published game:** https://claude.ai/artifact/Cf8gc3nNXwRqXrh7f3UHmd (version 10 = branch `clean-history`: the new look with one eye shine). To update it, read that artifact and then publish to the same `url`, so she keeps the same link. If no artifact tool is available, send her `dist/letter-trucks.html`.

## Layout
- `src/template.html` — the whole game in one file: canvas side-scroller plus DOM overlays, no framework. It has the placeholders `__LINES__`, `__VOICE__`, `__PICS__` and `__CREDITS__`.
- `src/pics/` — one picture per letter: Twemoji SVGs (CC BY 4.0), plus `igloo.svg`, which was drawn for this game.
- `voice/` — every spoken line and the tools that made it (see "Voice" below).
- `build.py` → `dist/letter-trucks.html`, about 5.5 MB because everything is embedded. Then run `node --check build/check.js`.
- `tests/` — Playwright (Python) tests. Run `python3 tests/mktest.py` first, which wraps the build with local fonts. Screenshots go to `tests/out/t/`. Tests: `test_v3.py` (full deliver and tow runs plus phone), `test_hint.py`, `test_touch.py` (touch play: the truck drives itself, a run is played only by tapping), `test_poke.py`, `test_portrait.py` (390×844 and phone landscape), `test_padpick.py` (truck picker with a fake controller). The game exposes `window.__lt` when the URL ends in `#debug`.
- **The repo is meant to be public: never put the kid's name (or other personal details) in code, docs, commits or voice lines.**
- Always look at the screenshots, not just the pass/fail output.

## Game design (decided with her; keep these)
- Two modes. **Bear deliveries:** a bear orders by picture and sound, and a crane drops the chosen box into the truck. **Tow truck:** hook the little-letter trailer whose big letter is waiting on the big truck. A run has a few stops, then ends with a party (deliver) or a parade (tow).
- Each stop is one deliberate choice: the truck stops and he has to pick. A wrong pick is kept short and plain so guessing isn't rewarding: the box wobbles "nope" where it sits (or the trailer hops) and says what it is, with no picture reveal. After 2 misses the right one glows.
- Per-letter levels: lvl 0 = name + sound, 2 choices; lvl ≥ 1 = sound only, up to 3 choices. Promote after 2 first-try correct answers; demote on a first-try miss. Letters he misses come back more often. Saved in localStorage (`letter-trucks-v3`, `letter-trucks-progress`).
- Letter sets, in order: Start (b k s m), Next (t j v l), Then (d z r f), More (p n h g), Short vowels (a e i o u), Last (c w y x q). Each set mixes letters that sound and look different; look-alikes and sound-alikes (b/d/p, d/t, m/n, k/c) sit in different sets so one is solid before its twin shows up. Within that, Treiman's letter-name research puts letters whose name holds their sound early. Bear deliveries never put sound-alikes side by side while a letter is new (`SOUNDALIKE`), and never c with k (same sound here); tow mode keeps look-alikes apart while new (`CONFUSE`). Old saved defaults (bdtp, wolf) move to the new Start set once (`settings.sets`). The default is Start; letters can be toggled one by one in the grown-up panel.
- Two-story a/g font (Fraunces). Uppercase is shown next to lowercase so he sees they're the same letter.
- **No faces on trucks** ("just trucks"). Customers are cute bears.
- **Look (she asked for Kakao Friends / LINE Friends vibes):** a flat pastel world with a warm brown outline (`INK`) on things he can touch. Bears are sticker style: a soft mochi-shaped head as big as the body, big shiny eyes set low, a little snout, stubby bent arms, a brown outline plus a white sticker edge with one soft shadow (`stickerEdge`). Bears are about truck height (`BS`); houses are small and sit beside the bear. Use `inked(w, fn)` to outline shapes drawn with `rr`/`circle`/`ell`, `fillP` for paths and `blob` for clusters (trees, bushes, clouds) so they get one outline. Bear preview page: https://claude.ai/artifact/6zt9bsPRNM7ZZMhCgRPqC4 (same code as the game).
- **Don't personalize with the kid's name, and no animal-pup mascot character.** She said this explicitly ("that's weird").
- Progress is shown as collecting (slots that fill with what he delivered), never as lives.
- **Touch has no on-screen controls** (she saw him get confused by having both arrows and tapping). The truck drives itself between stops once nobody's talking; at a stop he taps the box or trailer, and boxes bob gently when it's time to pick. Tapping the truck honks. Keyboard and controller still drive and pick by hand. The grown-up panel opens with a 1.5 s hold on the gear and has "Back to home screen".
- Works with touch, keyboard and controller (PS5/Steam). Portrait phone: the camera stays close on the choices, a card in the sky shows the customer and what they want (tap it to hear the order again), and the camera pans to the customer for the payoff. Landscape: the whole stop fits on screen.
- Extras: pick a truck before each game: four different kinds, each with its own horn (yellow dump truck=quack, red fire truck=ahooga, blue pickup=moo, green tractor=toot; all synthesized). `TRUCK_GEO` says where a box rides and where a bird lands on each kind; in tow mode they all get a hitch, music (can be turned off), things to poke (sun, clouds, trees, bushes, flowers, birds, cones, puddles, bears at finished stops), box reveals with bear reactions, hats (no bows) and houses, a bird that lands on the parked truck.

## Voice
- All audio is pre-generated and embedded in the page. **Never put an API key in the page or in the repo.** The OpenRouter key belongs in the environment as `OPENROUTER_API_KEY` (she has about $6.86 left of a $10 cap).
- `voice/lines.py` → `lines.json` and `voices.json` (249 lines). The narrator is Charon; the bears are Leda.
- `voice/tts_gen.py`: OpenRouter `/api/v1/audio/speech`, model `google/gemini-3.8-flash-tts`, PCM output only (24 kHz s16le). Every take is checked by two listener models (`google/gemini-3.8-flash`, `qwen/qwen3.8-omni-flash`). It then trims silence, caps pauses at 0.32 s and normalizes loudness to -17 LUFS. It writes a 56k original to `voice/originals/` and the game copy (atempo 1.1, 40k mono) to `voice/final/`. Usage: `python3 voice/tts_gen.py --only key1,key2 --takes 4`.
- Letter sounds use stutter spelling, e.g. "b-b-bus". Vowels: eh-eh-egg, ih-ih-igloo, ah-ah-octopus, uh-uh-umbrella. Also c→k-k-cat, q→kw-kw-queen, x→"fox, ks, ks". W is read as "Double U".
- The provider's content filter blocked "little D/P/F/H", so those lines say "little letter D" instead.
- The listener models can't judge vowel quality well. Formant checking (`voice/pick_vowels.py`, `voice/ana/`) is unreliable for the bear voice. A human should spot-check A/E/I/O/U.

## Open questions / ideas she's considering
- Playtest notes: he plays on her phone, used both arrows and tapping, and tended to pick left to right. She thinks he's guessing on everything rather than knowing the sounds. Not yet playtested: the self-driving truck and the quieter wrong pick.
- Glow-first is in, not yet playtested. The art overhaul (sticker bears, truck kinds, pastel world) is new too.
- Deliver boxes stay uppercase for now (one new thing at a time: the sound, on a letter he already knows); tow mode does upper to lower.
- Possible next features: a "first sounds" game (which box does the picture start with?), an installable offline app (PWA), and a grown-up progress page.
