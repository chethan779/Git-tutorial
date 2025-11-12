"""
mingle_game.py
Simple mingle/elimination mini-game prototype using pygame.

Controls (when you are in a room with the human player):
  - Arrow keys or WASD: move
  - SPACE: attempt attack when colliding with another player

How it works:
  - Players are split into groups (rooms) for a round.
  - Each room has a number of huts with limited capacity.
  - Players try to reach an empty spot inside a hut.
  - When huts fill, players may attack to take spots.
  - A 30s timer runs for each room; after timer ends, players not in huts are eliminated.
  - Survivors move to the next round. Repeat until only one (or no) players remain.
"""

import pygame
import random
import math
from collections import deque

# -------- CONFIGURATION --------
NUM_PLAYERS = 50            # total initial players
HUMAN_PLAYER_ID = 456       # ID that represents the human; one human exists if assigned to a room
ROOM_SIZE = 10              # preferred players per room (rooms computed from this)
ROUND_TIME = 30             # seconds per round
SCREEN_W, SCREEN_H = 800, 600
PLAYER_SPEED = 1.3
HUT_CAPACITY = 3            # spots per hut
HUT_COUNT = 1               # huts per room (increase to make it easier)
AI_ATTACK_CHANCE = 0.02     # per update chance to attempt attack if near somebody
# -------------------------------

pygame.init()
font = pygame.font.SysFont("Arial", 18)

# Simple Player class
class Player:
    def __init__(self, pid, pos, is_human=False):
        self.id = pid
        self.x, self.y = pos
        self.radius = 8
        self.color = (0, 180, 0) if not is_human else (200, 40, 40)
        self.is_human = is_human
        self.alive = True
        self.in_hut = False
        self.target_hut = None
        self.speed = PLAYER_SPEED if not is_human else PLAYER_SPEED * 1.2
        self.in_room = None  # reference to current Room
        self.last_attack_cooldown = 0

    def pos(self):
        return (self.x, self.y)

    def distance_to(self, x, y):
        return math.hypot(self.x - x, self.y - y)

    def update(self, dt, keys):
        if not self.alive or self.in_hut:
            return

        # human control fallback: movement keys
        if self.is_human:
            dx = dy = 0
            if keys.get(pygame.K_LEFT) or keys.get(pygame.K_a): dx -= 1
            if keys.get(pygame.K_RIGHT) or keys.get(pygame.K_d): dx += 1
            if keys.get(pygame.K_UP) or keys.get(pygame.K_w): dy -= 1
            if keys.get(pygame.K_DOWN) or keys.get(pygame.K_s): dy += 1
            if dx != 0 or dy != 0:
                norm = math.hypot(dx, dy)
                self.x += (dx / norm) * self.speed * dt
                self.y += (dy / norm) * self.speed * dt
            # keep inside room bounds
            self.x = max(self.in_room.bounds[0]+10, min(self.in_room.bounds[2]-10, self.x))
            self.y = max(self.in_room.bounds[1]+10, min(self.in_room.bounds[3]-10, self.y))
            return

        # AI behavior: if has target hut, move toward it, otherwise pick nearest hut
        if self.target_hut is None or self.target_hut.is_full() and not self.target_hut.contains(self):
            # pick a hut that has space if any, else random hut
            huts_with_space = [h for h in self.in_room.huts if not h.is_full()]
            if huts_with_space:
                self.target_hut = random.choice(huts_with_space)
            else:
                self.target_hut = random.choice(self.in_room.huts)

        # move toward a random empty spot of target_hut (or center)
        tx, ty = self.target_hut.get_spot_position()
        dx = tx - self.x
        dy = ty - self.y
        dist = math.hypot(dx, dy)
        if dist > 2:
            self.x += (dx / dist) * self.speed * dt
            self.y += (dy / dist) * self.speed * dt

        # small randomness
        if random.random() < 0.005:
            self.x += (random.random()-0.5)*2
            self.y += (random.random()-0.5)*2

# Hut with limited spots
class Hut:
    def __init__(self, x, y, capacity):
        self.x = x
        self.y = y
        self.capacity = capacity
        self.occupants = []

    def is_full(self):
        return len(self.occupants) >= self.capacity

    def contains(self, player):
        return player in self.occupants

    def try_enter(self, player):
        # If not full, occupy a spot
        if player in self.occupants:
            return True
        if not self.is_full():
            self.occupants.append(player)
            player.in_hut = True
            player.target_hut = self
            return True
        return False

    def force_replace(self, attacker):
        # Attacker tries to displace a random occupant
        if not self.occupants:
            return False
        victim = random.choice(self.occupants)
        # attacker replaces victim
        self.occupants.remove(victim)
        victim.in_hut = False
        victim.target_hut = None
        self.occupants.append(attacker)
        attacker.in_hut = True
        attacker.target_hut = self
        return victim

    def get_spot_position(self):
        # Return a small spot inside hut area (randomized per access)
        # huts are drawn as rectangles; spots are near center with jitter
        jitter = 10
        return (self.x + random.uniform(-jitter, jitter), self.y + random.uniform(-jitter, jitter))

# A Room contains players and huts and runs a timed round
class Room:
    def __init__(self, id, players, rect, hut_count=1, hut_capacity=HUT_CAPACITY):
        self.id = id
        self.players = players  # list of Player objects
        for p in players:
            p.in_room = self
            p.in_hut = False
            p.target_hut = None
        self.bounds = rect  # (x1,y1,x2,y2)
        self.huts = []
        self.elapsed = 0.0
        self.time_limit = ROUND_TIME
        self.active = True
        # generate huts inside bounds
        cx = (rect[0]+rect[2]) / 2
        cy = (rect[1]+rect[3]) / 2
        spacing = 30
        # place huts centered horizontally
        for i in range(hut_count):
            hx = cx + (i - (hut_count-1)/2) * (spacing + 60)
            hy = cy
            self.huts.append(Hut(hx, hy, hut_capacity))

    def update(self, dt, keys):
        if not self.active:
            return

        self.elapsed += dt
        # update players
        keys_state = pygame.key.get_pressed()
        keys_map = {k: keys_state[k] for k in range(len(keys_state))}
        for p in self.players:
            p.update(dt, keys_map)

        # simple collision checks: if a player is near a hut center, try to enter
        for p in self.players:
            if not p.alive or p.in_hut:
                continue
            for h in self.huts:
                if p.distance_to(h.x, h.y) < 18:
                    entered = h.try_enter(p)
                    if entered:
                        # snap into hut center
                        p.x, p.y = h.get_spot_position()
                        break
                    else:
                        # hut was full; allow occasional attack attempts (AI or human)
                        if p.is_human:
                            # human can press SPACE to attack nearby occupant (handled externally)
                            pass
                        else:
                            if random.random() < AI_ATTACK_CHANCE:
                                # try to force replace
                                victim = h.force_replace(p)
                                if victim:
                                    victim.alive = True  # victim is kicked out only (not dead yet)
                                    # the victim is now out of hut, will try to move away
                                    # slight random push
                                    victim.x += random.choice([-20,20])
                                    victim.y += random.choice([-20,20])
                                    # attacker occupies
                                    break

        # decrease alive players if time up
        if self.elapsed >= self.time_limit:
            # round ends: players not in huts are eliminated
            for p in self.players:
                if not p.in_hut:
                    p.alive = False
            self.active = False

    def draw(self, surface):
        # draw room bounds
        x1,y1,x2,y2 = self.bounds
        pygame.draw.rect(surface, (40,40,40), (x1,y1,x2-x1,y2-y1), 2)
        # title
        txt = font.render(f"Room {self.id}  Time left: {max(0,int(self.time_limit - self.elapsed))}s", True, (200,200,200))
        surface.blit(txt, (x1+6,y1+6))
        # draw huts
        for h in self.huts:
            hw, hh = 40, 30
            pygame.draw.rect(surface, (120, 80, 40), (h.x - hw//2, h.y - hh//2, hw, hh))
            cap_txt = font.render(f"{len(h.occupants)}/{h.capacity}", True, (255,255,255))
            surface.blit(cap_txt, (h.x - 18, h.y - 8))
        # draw players
        for p in self.players:
            if not p.alive:
                continue
            col = p.color
            if p.in_hut:
                col = (50, 120, 200)
            pygame.draw.circle(surface, col, (int(p.x), int(p.y)), p.radius)
            # show id small
            idtxt = font.render(str(p.id), True, (0,0,0))
            surface.blit(idtxt, (p.x - 6, p.y - 6))

# Utility: split players into rooms (list of lists)
def split_into_rooms(all_players, room_size):
    players = all_players[:]
    random.shuffle(players)
    rooms = []
    i = 0
    rid = 1
    while i < len(players):
        group = players[i:i+room_size]
        rooms.append((rid, group))
        i += room_size
        rid += 1
    return rooms

# Setup players
def create_players(num_players, human_id=None):
    players = []
    # we assign incremental IDs for bots; human gets special ID if requested and included
    next_id = 1
    human_assigned = False
    for i in range(num_players):
        pid = next_id
        next_id += 1
        is_human = False
        # decide one human: if human_id specified, set the player's id to that
        if (human_id is not None) and (not human_assigned):
            # set first player's id to human_id and mark as human; user "player" will be in some room randomly
            if random.random() < 0.02 or i == num_players - 1:  # ensure at least one attempt
                pid = human_id
                is_human = True
                human_assigned = True
        p = Player(pid, (0,0), is_human)
        players.append(p)
    # if human not assigned, replace first player's id with human
    if human_id and not human_assigned:
        players[0].id = human_id
        players[0].is_human = True
    return players

# Main game loop: conduct rounds until done
def run_game():
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Mingle Elimination Prototype")
    clock = pygame.time.Clock()

    all_players = create_players(NUM_PLAYERS, human_id=HUMAN_PLAYER_ID)
    round_number = 1

    # We'll keep a queue of players who are still alive
    survivors = [p for p in all_players if p.alive]

    running = True
    message_log = deque(maxlen=6)

    while running and len(survivors) > 1:
        # split survivors into rooms
        rooms_data = split_into_rooms(survivors, ROOM_SIZE)
        room_objs = []
        # layout rooms in grid (try to fit)
        cols = min(3, len(rooms_data))
        rows = max(1, math.ceil(len(rooms_data) / cols))
        margin = 12
        room_w = (SCREEN_W - (cols+1)*margin) / cols
        room_h = (SCREEN_H - (rows+1)*margin) / rows

        # create room objects
        for idx, (rid, group) in enumerate(rooms_data):
            col = idx % cols
            row = idx // cols
            x1 = int(margin + col*(room_w + margin))
            y1 = int(margin + row*(room_h + margin))
            rect = (x1, y1, int(x1 + room_w), int(y1 + room_h))
            # initialize player positions randomly within rect
            for p in group:
                p.x = random.uniform(rect[0]+20, rect[2]-20)
                p.y = random.uniform(rect[1]+20, rect[3]-20)
                p.alive = True
                p.in_hut = False
                p.target_hut = None
                p.in_room = None
            r = Room(rid, group, rect, hut_count=HUT_COUNT, hut_capacity=HUT_CAPACITY)
            room_objs.append(r)

        # run each room round sequentially (could be parallel but simpler sequential)
        for room in room_objs:
            message_log.append(f"Round {round_number} - Room {room.id} starting with {len(room.players)} players")
            round_running = True
            # run room until its timer expires
            while room.active and running:
                dt = clock.tick(60) / 16.0  # normalized delta
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    if event.type == pygame.KEYDOWN:
                        # human attack attempt: check collisions with others in same room
                        if event.key == pygame.K_SPACE:
                            # find human in this room
                            for p in room.players:
                                if p.is_human and p.alive and not p.in_hut:
                                    # try to attack nearby occupant in a hut
                                    for h in room.huts:
                                        if h.is_full() and p.distance_to(h.x, h.y) < 22:
                                            victim = h.force_replace(p)
                                            if victim:
                                                # victim gets kicked out and marked alive but not in hut
                                                message_log.append(f"You displaced player {victim.id}!")
                                                break

                keys = pygame.key.get_pressed()
                screen.fill((20,20,20))

                # update and draw room only (we render whole screen but focus on this room)
                room.update(dt, keys)
                # draw all rooms (but others are static until run)
                for ro in room_objs:
                    ro.draw(screen)

                # show messages and info
                y = SCREEN_H - 80
                for m in message_log:
                    screen.blit(font.render(m, True, (220,220,220)), (10, y))
                    y += 18

                pygame.display.flip()

            # after this room finishes, evaluate survivors
            survivors = [p for p in survivors if p.alive and (p in room.players and p.in_hut or p not in room.players and p.alive)]  # keep hut survivors in the room; others outside this room remain as they were
            # NOTE: since we're running rooms sequentially, players not in this room stay for later rooms as they were.
            # For simplicity, players who were in the room but not in huts have been marked alive=False in room update.
            message_log.append(f"Room {room.id} ended. Survivors: {sum(1 for p in room.players if p.alive)}")
        # after all rooms processed, recompute survivors globally
        survivors = [p for p in survivors if p.alive]
        round_number += 1
        # short pause between rounds
        pygame.time.delay(800)

    # Game end display
    screen.fill((10,10,10))
    if len(survivors) == 1:
        winner = survivors[0]
        txt = font.render(f"Winner: Player {winner.id} {'(YOU)' if winner.is_human else ''}", True, (255,255,0))
    else:
        txt = font.render("No winner (everyone eliminated?)", True, (255,255,0))
    screen.blit(txt, (SCREEN_W//2 - 150, SCREEN_H//2 - 20))
    pygame.display.flip()
    # wait a bit then quit
    pygame.time.wait(5000)
    pygame.quit()

if __name__ == "__main__":
    run_game()
