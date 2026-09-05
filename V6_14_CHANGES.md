# v6.14 — Intro v2 / startup optimization

- Rebuilt intro staging: castle -> Will close-up -> random second speaker close-up -> Phobos normal/cast -> transformation -> Phobos aftermath -> title -> menu.
- The on-screen character now always matches the speaker during character-specific dialogue.
- Transformation mode is selected once per intro: 50% all seven characters at once, 50% one random character.
- If a single character is selected, the transformation line is selected only from that character's dialogue pool.
- Horror Irma remains a 1-in-10 easter egg, only in Irma's single-character transformation path.
- Added normal/cast Phobos as preprocessed opaque-alpha assets; near-black robe pixels are no longer removed at runtime.
- Added build-time-preprocessed normal/transition/final intro sprites. Runtime no longer flood-fills large intro art.
- Gameplay SpriteSet is lazy-loaded only after NEW GAME, greatly reducing time before the first Pygame window/cutscene frame.
- Random intro choices are made once per scene/intro, never once per rendered frame.
- Added final Phobos audio pool in the intro using existing voice assets; the selected spoken line is shown as text and ducks intro music.
- Music folders remain external/flexible:
  - assets/audio/music/intro/opening/
  - assets/audio/music/intro/transformation/
  - assets/audio/music/intro/aftermath/
  - assets/audio/music/menu/
