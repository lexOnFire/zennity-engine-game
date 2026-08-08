# PHASE 8A PLAYTEST — VALIDAÇÃO MANUAL EM RUNTIME

**Status**: Interação automatizada indisponível para UI da Zennity Engine.  
**Ação Necessária**: Execute playtest manualmente seguindo estas instruções exatas.

---

## SETUP

1. Open the Zennity Engine project normally
2. Ensure all Step 1-7 assets are loaded (they should be in Assets/ folder)
3. Do NOT enter Play Mode yet

---

## ROUTE 1: VICTORY (FULL GAME FLOW)

**Duration**: ~8-12 minutes  
**What to observe**: Sprites, animations, camera, input, physics, combat, HUD, dialogue, scene transitions

### STEP 1A: Main Menu
```
1. In Project explorer, navigate to: Assets/Scenes/MainMenu.zscene
2. Double-click to load into editor
3. Click PLAY button (top center of editor)

EXPECTED:
✓ Black/dark screen appears
✓ Main Menu UI visible with title "ZENNITY ARENA"
✓ Three buttons: "NEW GAME" (blue), "CONTINUE" (gray), "EXIT" (red)
✓ Version label in bottom corner
✓ No errors in console

ACTUAL: [You observe]
```

### STEP 1B: New Game
```
4. Click NEW GAME button

EXPECTED:
✓ Scene transition begins
✓ Level1 loads (green-tinted arena)
✓ Player visible at center (white/blue sprite)
✓ 3 Enemy sprites visible (red, scattered around arena)
✓ 5 coin sprites visible (yellow, scattered)
✓ 1 key sprite visible (gold, upper-left area)
✓ 1 Guard NPC visible (brown, right side)
✓ 1 Door sprite visible (locked brown, right side)
✓ HUD visible in top-left: Health/Coins/Key labels
✓ No console errors

ACTUAL: [You observe]
```

### STEP 1C: Movement & Exploration
```
5. Press W, A, S, D keys to move Player around arena

EXPECTED:
✓ Player moves smoothly in all directions
✓ Player sprite faces correct direction (left/right)
✓ Diagonal movement does NOT accelerate diagonally (normalized)
✓ Camera follows Player smoothly (not jerky)
✓ Enemies move around arena (patrolling AI)
✓ Collider system prevents walking through walls
✓ No clipping or physics jitter

ACTUAL: [You observe]
```

### STEP 1D: Combat vs Enemies
```
6. Move Player near any Enemy
7. Press SPACE to attack

EXPECTED:
✓ Player plays Attack animation (0.4s, 4 frames)
✓ Enemy takes damage (health bar invisible, but disappears when dead)
✓ First hit doesn't kill immediately (Enemy has 100 HP, attack does 25 damage)
✓ After ~4 hits, Enemy sprite disappears (death)
✓ Repeat for all 3 enemies until all are dead
✓ Combat feels responsive (no input lag)

ACTUAL: [You observe]
```

### STEP 1E: Collect Coins
```
8. Move Player over each coin sprite
9. Walk into coin (no button press needed, trigger collision)

EXPECTED:
✓ Coin sprite disappears on contact
✓ CoinsLabel in HUD updates: "Coins: 1" → "Coins: 2" etc.
✓ Collect all 5 coins
✓ Final HUD shows "Coins: 5"
✓ No sound (audio not in benchmark)

ACTUAL: [You observe]
```

### STEP 1F: Collect Key
```
10. Move Player to upper-left area where key is visible
11. Walk into key sprite

EXPECTED:
✓ Key sprite disappears
✓ KeyLabel in HUD updates: "Key: No" → "Key: Yes"
✓ No animation or sound (simplicity)

ACTUAL: [You observe]
```

### STEP 1G: Guard Dialogue (Condition Check)
```
12. Move Player to right side near Guard NPC
13. Press E key when near Guard (interaction zone is 3x3 collider)

EXPECTED:
✓ Dialogue window appears (modal or bottom-screen)
✓ Text: "You found the key. You may pass."
✓ OR if you didn't collect key first: "Find the key and come back."
✓ Dialogue closes (on button click or E press again)
✓ If has_key==true, dialogue event "open_gate" fired

ACTUAL: [You observe]
```

### STEP 1H: Door Unlock
```
14. Observe Door sprite (should be locked brown color initially)
15. After Guard dialogue with has_key==true, Door should change appearance

EXPECTED:
✓ Door sprite changes to unlocked appearance (door_open.png, lighter color)
✓ Door collider becomes disabled (Player can walk through)
✓ No collision when walking through door area
✓ Door visual confirms unlock

ACTUAL: [You observe]
```

### STEP 1I: Level Exit & Autosave
```
16. Move Player to far right, past Door
17. Walk into Level Exit trigger zone

EXPECTED:
✓ Scene transition begins
✓ Brief loading (optional fade)
✓ Level2 loads (darker arena, similar layout)
✓ Player spawns at center (same position as Level1)
✓ Boss visible at right side (large red sprite, ~1.5x scale)
✓ HUD shows: Health, Coins still 5 (persistent), BossHealthBar visible
✓ BossNameLabel shows "Boss: Alive" in red
✓ Autosave occurred (no visible notification, but saved to disk)

ACTUAL: [You observe]
```

### STEP 1J: Boss Phase 1 (High Health)
```
18. Move Player toward Boss (Boss at 500 HP initially)
19. Boss should begin chasing when Player within 500 units
20. Attack Boss with SPACE when within attack range (72 units)

EXPECTED:
✓ Boss sprite becomes visible and begins moving
✓ Boss chases Player (20 movement speed, not too fast)
✓ Boss animation: Idle → Run (smooth transition)
✓ Boss attacks when Player in range (red attack animation, 0.5s)
✓ Each Boss hit does 20 damage to Player
✓ Player HUD health decreases
✓ Boss HUD (BossHealthBar) shows damage (red bar shrinks)
✓ Continue attacking Boss, Player health ~100 → 80 → 60 etc.
✓ Dodge boss attacks by moving away
✓ After ~10 successful Player attacks, Boss health reaches 250 (50%)

ACTUAL: [You observe]
```

### STEP 1K: Boss Phase 2 (Low Health Transition)
```
21. Continue attacking as Boss health reaches 250 HP (50% threshold)

EXPECTED:
✓ Boss transitions automatically (no animation, just stat change)
✓ Boss movement speed increases visibly (120 vs 80, +50%)
✓ Boss attacks more frequently (0.8s cooldown vs 1.5s, feels aggressive)
✓ Boss attacks change: normal attacks + occasional heavy attacks
✓ Heavy attack animation different from normal (0.7s, more intense)
✓ Heavy attack damage: 35 HP vs normal 20 HP
✓ Boss HUD shows remaining health (red bar getting very low)
✓ Player strategy: dodge heavy attacks, attack during cooldown

ACTUAL: [You observe]
```

### STEP 1L: Boss Death
```
22. Continue attacking until Boss health reaches 0

EXPECTED:
✓ Boss stops moving
✓ Boss plays death animation (1.0s non-looping)
✓ Death animation completes
✓ Scene automatically transitions to Victory.zscene
✓ Brief fade/loading (optional)
✓ Victory screen appears

ACTUAL: [You observe]
```

### STEP 1M: Victory Screen
```
23. Victory screen loads automatically after Boss death

EXPECTED:
✓ Dark background (purplish tone)
✓ Large "VICTORY" title in green (72pt)
✓ "Boss Defeated!" subtitle
✓ Score display: "Score: 0" (or actual score value)
✓ Coins display: "Coins: 5" (persisted from Level1)
✓ Two buttons: "MAIN MENU" (blue), "NEW GAME" (green)
✓ All text readable and centered
✓ No console errors

ACTUAL: [You observe]
```

### STEP 1N: Return to Main Menu from Victory
```
24. Click MAIN MENU button on Victory screen

EXPECTED:
✓ Scene transition to MainMenu
✓ Main Menu UI appears again
✓ HUD from Level2 is gone
✓ Victory UI is gone
✓ All state reset (for fresh "New Game" next time)
✓ Continue button is now ENABLED (gray → blue, because autosave exists)

ACTUAL: [You observe]
```

**ROUTE 1 RESULT**: ✅ PASS / ❌ FAIL

---

## ROUTE 2: GAME OVER / RETRY

**Duration**: ~4 minutes  
**What to test**: Death condition, GameOver scene, retry flow, state cleanup

### STEP 2A: Start New Game
```
1. From Main Menu, click NEW GAME
2. Level1 loads
3. (Optional: skip to Level2 by console or load Level2 directly)

EXPECTED:
✓ Level1 or Level2 loads successfully
✓ Player spawns with health: 100
✓ No enemies attacking immediately (they spawn idle)
```

### STEP 2B: Trigger Player Death (Level1)
```
4. In Level1, allow enemies to attack Player:
   - Move toward enemies without attacking back
   - Let them hit Player repeatedly
   - Do NOT move away (stay in combat)

EXPECTED:
✓ Player health decreases with each enemy hit (each hit -10 damage)
✓ HealthLabel updates: "Health: 100" → "90" → "80" etc.
✓ HealthBar shrinks (green bar gets smaller)
✓ After 10 hits, player health reaches 0
✓ Player sprite might play damage animation (if implemented)
```

### STEP 2C: GameOver Loads
```
5. Player health reaches 0

EXPECTED:
✓ Scene immediately transitions (no delay)
✓ Level1 gameplay stops (no more input processing)
✓ GameOver.zscene loads
✓ Dark red background
✓ Large "GAME OVER" title (red, 72pt)
✓ Two buttons: "RETRY" (blue), "MAIN MENU" (brown)
✓ No Level1 UI visible
✓ Console clean

ACTUAL: [You observe]
```

### STEP 2D: Retry
```
6. Click RETRY button

EXPECTED:
✓ Scene transition to Level1
✓ Level1 loads fresh (Player at center, enemies still alive and positioned)
✓ Player health reset to 100
✓ HUD: "Health: 100"
✓ Coins reset to 0 (or reflects autosave point)
✓ Key reset to false (or reflects autosave point)
✓ GameOver UI completely gone
✓ Enemies don't have residual health (fresh state)
✓ No dialogue/events from previous run active
✓ Previous boss_defeated flag reset

ACTUAL: [You observe]
```

### STEP 2E: Death in Level2 (Optional, if time permits)
```
7. Load Level2 directly (or progress through Level1 again)
8. Let Boss kill Player (similar to Step 2B)

EXPECTED:
✓ Same GameOver behavior (no special case for Level2)
✓ Retry reloads Level2 fresh
✓ Boss health reset to 500
✓ No boss_defeated flag set
```

**ROUTE 2 RESULT**: ✅ PASS / ❌ FAIL

---

## ROUTE 3: SAVE / STOP / CONTINUE

**Duration**: ~5 minutes  
**What to test**: Autosave persistence, Stop/Play cycle, Continue load, state restoration

### STEP 3A: Progress to Level2 (Autosave Point)
```
1. From Main Menu, click NEW GAME
2. Level1 loads
3. Collect coins (or don't, up to you)
4. Collect key
5. Interact with Guard (E key)
6. Walk through unlocked door
7. Enter Level Exit trigger

EXPECTED:
✓ Autosave occurs at Level Exit (no visual feedback required)
✓ Level2 loads
✓ Player visible at center
✓ Boss visible at right

ACTUAL: [You observe]
```

### STEP 3B: Stop Playtest
```
8. Click STOP button (top center of editor, opposite of PLAY)

EXPECTED:
✓ Play Mode ends
✓ Editor returns to edit mode
✓ Runtime state cleared
✓ Game paused/stopped
✓ No gameplay running
```

### STEP 3C: Restart Play Mode (Fresh)
```
9. Click PLAY button again (without changing scene or doing anything else)

EXPECTED:
✓ Play Mode starts fresh
✓ Current scene in editor is loaded
   - If still in Level2: Level2 loads
   - If back in MainMenu: MainMenu loads
✓ No runtime state from previous session
✓ Clean slate

ACTUAL: [You observe]
```

### STEP 3D: Continue from Autosave
```
10. Navigate back to MainMenu if not there (or stay if Level2)
11. From MainMenu, click CONTINUE button

EXPECTED:
✓ CONTINUE button is ENABLED (no longer gray)
✓ Click loads previous autosave point
✓ Level2 loads (the autosaved scene)
✓ Player at same position (or respawn center, depends on autosave policy)
✓ Coins still reflect Level1 collection (if autosave includes project variables)
✓ Key state persists (has_key = true from collected key)
✓ Health restored (or respawned at 100, depends on autosave policy)
✓ Boss at 500 HP (fresh, not damaged from previous session)
✓ BossHealthBar at 100% (full red bar)

ACTUAL: [You observe]
```

### STEP 3E: Verify No State Pollution
```
12. From Continue's loaded scene, observe for residual state:
    - No old dialogue boxes open
    - No enemy from Level1 visible
    - No coin sprites (already collected)
    - No key sprite (already collected)
    - All event listeners fresh (Guard won't re-trigger dialogue)

EXPECTED:
✓ Level2 is clean (only Boss, Player, Camera, HUD, walls)
✓ No Level1 remnants
✓ No stale event registrations
✓ Gameplay can proceed normally

ACTUAL: [You observe]
```

**ROUTE 3 RESULT**: ✅ PASS / ❌ FAIL

---

## DETAILED OBSERVATION CHECKLIST

Record PASS/FAIL for each subsystem:

### Visual Rendering
- [ ] Player sprite visible and correct
- [ ] Enemy sprites visible and correct (3 in Level1, 1 in Level2)
- [ ] Coin sprites visible (5 in Level1)
- [ ] Key sprite visible (1 in Level1)
- [ ] Guard NPC sprite visible (1 in Level1)
- [ ] Door sprite visible and changes appearance on unlock
- [ ] Boss sprite visible and correct scale (1.5x in Level2)
- [ ] HUD elements visible and readable
- [ ] UI buttons respond to mouse hover (visual feedback)
- [ ] No texture corruption or missing sprites
- [ ] Colors accurate (green Victory, red GameOver, etc.)

**VISUAL RENDERING**: ✅ PASS / ❌ FAIL

### Input
- [ ] WASD movement responds immediately
- [ ] SPACE attack fires on press (no delay)
- [ ] E key interaction triggers (Guard dialogue)
- [ ] Mouse clicks on buttons work
- [ ] No input buffer issues (commands don't queue)
- [ ] Can move while holding attack button
- [ ] Direction changes respond smoothly

**INPUT**: ✅ PASS / ❌ FAIL

### Physics
- [ ] Player can't walk through walls
- [ ] Collider sizes match sprite visuals (no too-large/too-small)
- [ ] Enemies blocked by walls
- [ ] Boss blocked by walls
- [ ] Trigger colliders work (coins, key, interaction zones)
- [ ] Physics simulation smooth (no stutter)
- [ ] Gravity scale = 0 (no falling)
- [ ] Door collider properly enables/disables

**PHYSICS**: ✅ PASS / ❌ FAIL

### Animation
- [ ] Player Idle animation plays smoothly (3-frame loop)
- [ ] Player Run animation plays smoothly (speed-based)
- [ ] Player Attack animation plays (0.4s, 4 frames)
- [ ] Enemy Idle animation plays
- [ ] Enemy Run animation plays (chasing)
- [ ] Enemy Attack animation plays
- [ ] Enemy Death animation plays (when health=0)
- [ ] Boss Idle/Run/Attack/HeavyAttack animations play
- [ ] Boss Death animation plays (1.0s)
- [ ] Animation speed-based transitions work (speed > 0.1 → Run)
- [ ] No animation jitter or frame skips

**ANIMATION**: ✅ PASS / ❌ FAIL

### Camera
- [ ] Camera follows Player smoothly
- [ ] Camera centered on Player at all times
- [ ] Camera doesn't lag behind Player (smooth_follow=true works)
- [ ] No camera clipping through objects
- [ ] Viewport shows correct area (1280x720)
- [ ] Camera speed reasonable (follow_speed=5.0)

**CAMERA**: ✅ PASS / ❌ FAIL

### Combat
- [ ] Player attack hits enemy (raycast works)
- [ ] Enemy damage reduces health
- [ ] Enemy dies after sufficient damage (~4 hits)
- [ ] Attack range enforced (can't hit beyond 64 units)
- [ ] Enemy counterattacks when close
- [ ] Enemy damage reduces Player health
- [ ] Attack animation + hit event coordination works
- [ ] No friendly fire (raycast ignores self)
- [ ] Multiple enemies can be attacked sequentially

**COMBAT**: ✅ PASS / ❌ FAIL

### Enemy AI
- [ ] Enemy detects Player (range=300)
- [ ] Enemy chases when detected
- [ ] Enemy stops when in attack range (48 units)
- [ ] Enemy attacks at cooldown (1.0s between attacks)
- [ ] Enemy patrols when Player not detected
- [ ] Multiple enemies don't interfere with each other
- [ ] Pathfinding avoids walls (or bounces off naturally)
- [ ] AI feels reasonable difficulty (not too easy, not unfair)

**ENEMY AI**: ✅ PASS / ❌ FAIL

### Boss AI
- [ ] Boss detects Player (range=500)
- [ ] Boss chases Player (speed=80 Phase1, speed=120 Phase2)
- [ ] Boss attacks at range (72 units)
- [ ] Boss cooldown works (1.5s Phase1, 0.8s Phase2)
- [ ] Phase transition happens at 250 HP (50%)
- [ ] Phase 2 visibly faster (movement and attack frequency)
- [ ] Phase 2 heavy attacks feel different
- [ ] Boss doesn't get stuck on walls
- [ ] Boss difficulty feels appropriate (challenging, not impossible)

**BOSS**: ✅ PASS / ❌ FAIL

### HUD / UI
- [ ] HealthLabel shows "Health: X" (updates correctly)
- [ ] HealthBar shows green progress bar
- [ ] CoinsLabel shows "Coins: X" (updates on pickup)
- [ ] KeyLabel shows "Key: Yes/No" (updates correctly)
- [ ] BossHealthBar visible in Level2 (red bar)
- [ ] BossNameLabel shows "Boss: Alive" (red text)
- [ ] All labels readable (font size, color contrast)
- [ ] Buttons respond to clicks (no dead zones)
- [ ] Victory score and coins display correctly
- [ ] GameOver buttons work

**UI**: ✅ PASS / ❌ FAIL

### Dialogue
- [ ] Guard interaction triggers dialogue (E key)
- [ ] Dialogue appears in expected location
- [ ] Condition works (has_key==true shows "pass" message, false shows "find key")
- [ ] Dialogue closes on interaction
- [ ] Open_gate event fires (door unlocks after)
- [ ] No dialogue crashes or hangs

**DIALOGUE**: ✅ PASS / ❌ FAIL

### Scene Management
- [ ] MainMenu loads correctly
- [ ] Level1 loads from MainMenu
- [ ] Level2 loads from Level1
- [ ] Victory loads from Level2
- [ ] GameOver loads on player death
- [ ] Retry loads Level1 fresh
- [ ] Continue loads Level2 from autosave
- [ ] Scene transitions smooth (no stutter)
- [ ] No double-loading or infinite loops

**SCENE MANAGEMENT**: ✅ PASS / ❌ FAIL

### Save/Load
- [ ] Autosave occurs at Level Exit
- [ ] Continue button enabled after autosave
- [ ] Continue loads correct scene (Level2)
- [ ] Continue restores coins count
- [ ] Continue restores key state
- [ ] New Game resets state properly
- [ ] Stop/Play cycle doesn't corrupt save

**SAVE/LOAD**: ✅ PASS / ❌ FAIL

### Audio
- [ ] (Optional: not in benchmark)
- [ ] Boss music plays in Level2 (if implemented)
- [ ] Victory music plays on victory (if implemented)

**AUDIO**: ✅ PASS / ❌ N/A (NOT REQUIRED)

---

## BUG REPORT TEMPLATE

If you find any issue, record it here:

### BUG #1
```
SYSTEM: [Movement / Combat / AI / HUD / Dialogue / Scene / etc]
EXPECTED: [What should happen]
ACTUAL: [What actually happened]
REPRODUCTION: [Steps to reproduce]
  1. [Step 1]
  2. [Step 2]
  3. [Step 3]
SEVERITY: P0 (Blocker) / P1 (Major) / P2 (Minor)
ROOT CAUSE: [If identified]
PROPOSED FIX: [If identified]
```

---

## FINAL VERDICT

After completing all three routes, report:

```
═══════════════════════════════════════════════════════════════

ROUTE 1 — VICTORY:               ✅ PASS / ❌ FAIL
ROUTE 2 — GAME OVER / RETRY:     ✅ PASS / ❌ FAIL
ROUTE 3 — SAVE / STOP / CONTINUE: ✅ PASS / ❌ FAIL

VISUAL RENDERING:   ✅ PASS / ❌ FAIL
INPUT:              ✅ PASS / ❌ FAIL
PHYSICS:            ✅ PASS / ❌ FAIL
ANIMATION:          ✅ PASS / ❌ FAIL
CAMERA:             ✅ PASS / ❌ FAIL
COMBAT:             ✅ PASS / ❌ FAIL
ENEMY AI:           ✅ PASS / ❌ FAIL
BOSS:               ✅ PASS / ❌ FAIL
UI:                 ✅ PASS / ❌ FAIL
DIALOGUE:           ✅ PASS / ❌ FAIL
SCENE MANAGEMENT:   ✅ PASS / ❌ FAIL
SAVE/LOAD:          ✅ PASS / ❌ FAIL
AUDIO:              ✅ PASS / ❌ N/A

BUGS FOUND:
  P0: [Count / List]
  P1: [Count / List]
  P2: [Count / List]

═══════════════════════════════════════════════════════════════

FINAL DECLARATION:

If all routes PASS and all subsystems PASS:

✅ ZENNITY ARENA: PLAYABLE
   Zennity Engine successfully builds and runs a complete 2D action game.
   Full game loop from Main Menu to Victory is functional.

✅ ZENNITY ENGINE VISUAL GAMEPLAY BENCHMARK: PASSED
   Complex game mechanics (movement, combat, AI, boss phases, dialogue,
   progression, save/load) work correctly without any Python gameplay scripts.
   100% visual gameplay proven in runtime.

If any route FAILS or critical subsystem FAILS:

❌ ZENNITY ARENA: NOT FULLY PLAYABLE
   [List which routes/systems failed]
   [List blocking bugs]
   
Recommendation: Fix blocking bugs and re-test before declaring success.

═══════════════════════════════════════════════════════════════
```

---

## INSTRUCTIONS TO BEGIN

1. Open Zennity Engine project normally
2. Navigate to Assets/Scenes/MainMenu.zscene
3. Double-click to load
4. Click PLAY button
5. Begin Route 1 from STEP 1A above
6. Record observations at each step
7. Complete all three routes
8. Fill in FINAL VERDICT
9. Report results

**Do NOT skip steps. Do NOT approximate. Record exactly what you observe.**

**Do NOT modify code based on test results. Only record bugs — we fix after playtest.**

Begin playtest now. Expected duration: 20-30 minutes total.
