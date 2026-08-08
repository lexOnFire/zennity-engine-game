# PHASE 8A: REAL GAME BENCHMARK - PROJECT PLAN

**Date**: 2026-08-08  
**Goal**: Build a complete small 2D game using ONLY visual systems  
**Game**: Zennity Arena Demo (2D Top-Down Action)

## Project Structure

```
Assets/
├── Scenes/
│   ├── MainMenu.zscene (visual scene)
│   ├── Level1.zscene
│   ├── Level2.zscene
│   ├── GameOver.zscene
│   └── Victory.zscene
│
├── UI/
│   ├── MainMenu.zui
│   ├── HUD.zui
│   ├── GameOver.zui
│   └── Victory.zui
│
├── Dialogues/
│   └── GuardDialogue.zdialogue (existing or new)
│
├── Prefabs/
│   ├── Player/
│   ├── Enemy/
│   ├── Coin/
│   └── Key/
│
├── Audio/
│   ├── music/
│   └── sfx/
│
└── Animations/
    ├── PlayerController.zcontroller
    ├── EnemyController.zcontroller
    └── BossController.zcontroller
```

## Game Flow

```
MainMenu
  ↓
New Game → Reset State → Load Level1
Continue → Load Game → Load LastScene
  ↓
Level1 Gameplay
  ├─ Player Movement (WASD)
  ├─ Camera Follow
  ├─ Enemies (3-5)
  ├─ Combat (SPACE to attack)
  ├─ Health System
  ├─ Coins (5)
  ├─ Key (1)
  ├─ Guard NPC (Dialogue)
  └─ Door (locked until key)
  ↓
Level2 Gameplay
  ├─ Harder Enemies
  ├─ Boss
  └─ Final Objective
  ↓
Victory Scene
  ├─ Score Display
  ├─ Return to Menu
  └─ Save Score
  
  OR
  
Game Over Scene (Player Dies)
  ├─ Retry (Load Checkpoint)
  ├─ Main Menu
  └─ Restart Game
```

## Core Systems to Validate

1. **Input System** - WASD movement, SPACE attack, E dialogue
2. **Physics** - Movement, collision, damage detection
3. **Camera** - Follow player, smooth movement
4. **Animation** - Idle/Run/Attack/Hit/Death states
5. **Combat** - Attack hitbox, enemy damage, death
6. **UI** - HUD (health bar, coins, key indicator)
7. **Audio** - Music, SFX (attack, hit, pickup, dialogue)
8. **Dialogue** - Guard NPC, choice-based interactions
9. **Scene Management** - Loading, unloading, checkpoint
10. **Save/Load** - Game state persistence

## Milestones

- [ ] Step 1: Project Structure Created
- [ ] Step 2: Main Menu Built
- [ ] Step 3-5: Level 1 Scenes Created
- [ ] Step 6-17: Player Systems (Movement, Camera, Animation, Combat)
- [ ] Step 18-21: Enemy & NPC Systems
- [ ] Step 22-26: Level 2 & Victory/GameOver
- [ ] Step 27-29: Save/Load & E2E Tests
- [ ] Step 30-42: Full Audit & Report

## Key Constraints

- ✅ NO Python gameplay scripts
- ✅ NO hardcoded values in code
- ✅ Use Logic Graph for ALL gameplay logic
- ✅ Use real asset formats (.zscene, .zui, .zdialogue, .zcontroller)
- ✅ Document all bugs/gaps found
- ✅ Register UX issues (don't silently fix)
- ✅ Test full game runs (3 main routes)

## Status

Starting Phase 8A implementation...
