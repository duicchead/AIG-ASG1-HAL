import pygame

from random import randint, random
from Graph import *

from Character import *
from State import *


class Archer_TeamA(Character):

    def __init__(self, world, image, projectile_image, base, position):

        Character.__init__(self, world, "archer", image)

        self.projectile_image = projectile_image

        self.base = base
        self.position = position
        self.move_target = GameEntity(world, "archer_move_target", None)
        self.target = None
        self.level = 0

        self.maxSpeed = 50
        self.min_target_distance = 100
        self.projectile_range = 100
        self.projectile_speed = 100

        seeking_state = ArcherStateSeeking_TeamA(self)
        kiting_state = ArcherStateKiting_TeamA(self)
        attacking_state = ArcherStateAttacking_TeamA(self)
        ko_state = ArcherStateKO_TeamA(self)

        self.brain.add_state(seeking_state)
        self.brain.add_state(kiting_state)
        self.brain.add_state(attacking_state)
        self.brain.add_state(ko_state)

        self.brain.set_state("seeking")

    def render(self, surface):

        Character.render(self, surface)

    def process(self, time_passed):

        Character.process(self, time_passed)

        level_up_stats = ["hp", "speed", "ranged damage",
                          "ranged cooldown", "projectile range"]
        if self.can_level_up():
            self.level += 1
            #choice = randint(0, len(level_up_stats) - 1)
            if self.level >= 2:
                self.level_up(level_up_stats[3])
            else:
                self.level_up(level_up_stats[3])


class ArcherStateSeeking_TeamA(State):

    def __init__(self, archer):

        State.__init__(self, "seeking")
        self.archer = archer

        self.archer.path_graph = self.archer.world.paths[randint(
            0, len(self.archer.world.paths)-1)]

    def do_actions(self):
        

        self.archer.velocity = self.archer.move_target.position - self.archer.position
        if self.archer.velocity.length() > 0:
            self.archer.velocity.normalize_ip()
            self.archer.velocity *= self.archer.maxSpeed

        nearest_opponent = self.archer.world.get_nearest_opponent(self.archer)
        opponent_distance = (self.archer.position -
                             nearest_opponent.position).length()
        #if opponent_distance > 270 and self.archer.current_hp < 150:
        if opponent_distance > 250 and self.archer.current_hp < self.archer.max_hp:
            self.archer.heal()

    def check_conditions(self):
        # if self.archer.current_hp < 50:
        # self.archer.heal()

        #if near enemy base and knight is there to tank, target tower/base only
        is_knight_nearby = self.archer.world.get_all_nearby_opponents(self.archer)
        enemy_base = self.archer.world.enemy_base(self.archer)
        enemy_tower = self.archer.world.nearest_enemy_tower(self.archer)
        enemy_spawn_pos = enemy_base.spawn_position
        enemy_spawn_pos_distance = (self.archer.position - enemy_spawn_pos).length()

        if enemy_spawn_pos_distance <= 250 and is_knight_nearby == 1:
            if enemy_tower is not None:
                self.archer.target = enemy_tower
                return "attacking"
            else:
                self.archer.target = enemy_base
                return "attacking"


        # check if opponent is in range
        else:
            nearest_opponent = self.archer.world.get_nearest_opponent(self.archer)
            if nearest_opponent is not None:
                opponent_distance = (self.archer.position -
                                    nearest_opponent.position).length()
                if opponent_distance <= self.archer.min_target_distance:
                    self.archer.target = nearest_opponent
                    return "attacking"

        if (self.archer.position - self.archer.move_target.position).length() < 8:

            # continue on path
            if self.current_connection < self.path_length:
                self.archer.move_target.position = self.path[self.current_connection].toNode.position
                self.current_connection += 1

        return None

    def entry_actions(self):

        nearest_node = self.archer.path_graph.get_nearest_node(
            self.archer.position)

        self.path = pathFindAStar(self.archer.path_graph,
                                  nearest_node,
                                  self.archer.path_graph.nodes[self.archer.base.target_node_index])

        self.path_length = len(self.path)

        if (self.path_length > 0):
            self.current_connection = 0
            self.archer.move_target.position = self.path[0].fromNode.position

        else:
            self.archer.move_target.position = self.archer.path_graph.nodes[
                self.archer.base.target_node_index].position


class ArcherStateKiting_TeamA(State):
    def __init__(self, archer):

        State.__init__(self, "kiting")
        self.archer = archer

    def do_actions(self):

        self.archer.velocity = self.archer.position - self.archer.target.position
        if self.archer.velocity.length() > 0:
            self.archer.velocity.normalize_ip()
            self.archer.velocity *= self.archer.maxSpeed

    def check_conditions(self):
        # larger number, longer it takes for archer to escape kiting state and go back to attacking. 1.75 just nice?
        if self.archer.current_ranged_cooldown <= self.archer.ranged_cooldown / 1.7:
            return "attacking"

    def entry_actions(self):

        return None


class ArcherStateAttacking_TeamA(State):

    def __init__(self, archer):

        State.__init__(self, "attacking")
        self.archer = archer

    def do_actions(self):
        


        opponent_distance = (self.archer.position -
                             self.archer.target.position).length()

        # opponent within range
        if opponent_distance <= self.archer.min_target_distance:
            self.archer.velocity = Vector2(0, 0)
            if self.archer.current_ranged_cooldown <= 0:
                self.archer.ranged_attack(self.archer.target.position)

        else:
            self.archer.velocity = self.archer.target.position - self.archer.position
            if self.archer.velocity.length() > 0:
                self.archer.velocity.normalize_ip()
                self.archer.velocity *= self.archer.maxSpeed

    def check_conditions(self):
        nearest_opponent = self.archer.world.get_nearest_opponent(self.archer)
        opponent_distance = (self.archer.position -
                             nearest_opponent.position).length()

        # target is gone
        if self.archer.world.get(self.archer.target.id) is None or self.archer.target.ko:
            self.archer.target = None
            return "seeking"

        # opponent within range
        #opponent_distance = (self.archer.position - self.archer.target.position).length()
        # if opponent_distance <= self.archer.min_target_distance:
        if nearest_opponent.max_hp == 400 or nearest_opponent.max_hp == 100 and opponent_distance <= self.archer.min_target_distance:
            if self.archer.current_ranged_cooldown == self.archer.ranged_cooldown:
                self.archer.target = nearest_opponent
                return "kiting"

        return None

    def entry_actions(self):

        return None


class ArcherStateKO_TeamA(State):

    def __init__(self, archer):

        State.__init__(self, "ko")
        self.archer = archer

    def do_actions(self):

        return None

    def check_conditions(self):

        # respawned
        if self.archer.current_respawn_time <= 0:
            self.archer.current_respawn_time = self.archer.respawn_time
            self.archer.ko = False
            self.archer.path_graph = self.archer.world.paths[randint(
                0, len(self.archer.world.paths)-1)]
            return "seeking"

        return None

    def entry_actions(self):

        self.archer.current_hp = self.archer.max_hp
        self.archer.position = Vector2(self.archer.base.spawn_position)
        self.archer.velocity = Vector2(0, 0)
        self.archer.target = None

        return None
