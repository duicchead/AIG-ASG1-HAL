import pygame

from random import randint, random
from Graph import *

from Character import *
from State import *


class Wizard_TeamA(Character):

    def __init__(self, world, image, projectile_image, base, position, explosion_image=None):

        Character.__init__(self, world, "wizard", image)

        self.projectile_image = projectile_image
        self.explosion_image = explosion_image

        self.base = base
        self.position = position
        self.move_target = GameEntity(world, "wizard_move_target", None)
        self.target = None
        self.level = 0

        self.maxSpeed = 50
        self.min_target_distance = 100
        self.projectile_range = 100
        self.projectile_speed = 100

        seeking_state = WizardStateSeeking_TeamA(self)
        attacking_state = WizardStateAttacking_TeamA(self)
        ko_state = WizardStateKO_TeamA(self)
        kiting_state = WizardStateKiting_TeamA(self)

        self.brain.add_state(seeking_state)
        self.brain.add_state(attacking_state)
        self.brain.add_state(ko_state)
        self.brain.add_state(kiting_state)

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


class WizardStateSeeking_TeamA(State):

    def __init__(self, wizard):

        State.__init__(self, "seeking")
        self.wizard = wizard

        self.wizard.path_graph = self.wizard.world.paths[randint(
            0, len(self.wizard.world.paths)-1)]

    def do_actions(self):

        self.wizard.velocity = self.wizard.move_target.position - self.wizard.position
        if self.wizard.velocity.length() > 0:
            self.wizard.velocity.normalize_ip()
            self.wizard.velocity *= self.wizard.maxSpeed

        nearest_opponent = self.wizard.world.get_nearest_opponent(self.wizard)
        opponent_distance = (self.wizard.position -
                             nearest_opponent.position).length()

        if opponent_distance > 200 and self.wizard.current_hp < self.wizard.max_hp:
            self.wizard.heal()

    def check_conditions(self):
        nearest_opponent = self.wizard.world.get_nearest_opponent(self.wizard)
        opponent_distance = (self.wizard.position -
                             nearest_opponent.position).length()
        #if opponent_distance > 300 and self.wizard.current_hp < 100:
            #self.wizard.heal()

        # check if opponent is in range
        nearest_opponent = self.wizard.world.get_nearest_opponent(self.wizard)
        if nearest_opponent is not None:
            opponent_distance = (self.wizard.position -
                                 nearest_opponent.position).length()
            if opponent_distance <= self.wizard.min_target_distance:
                self.wizard.target = nearest_opponent
                return "attacking"

        if (self.wizard.position - self.wizard.move_target.position).length() < 8:

            # continue on path
            if self.current_connection < self.path_length:
                self.wizard.move_target.position = self.path[self.current_connection].toNode.position
                self.current_connection += 1

        return None

    def entry_actions(self):

        nearest_node = self.wizard.path_graph.get_nearest_node(
            self.wizard.position)

        self.path = pathFindAStar(self.wizard.path_graph,
                                  nearest_node,
                                  self.wizard.path_graph.nodes[self.wizard.base.target_node_index])

        self.path_length = len(self.path)

        if (self.path_length > 0):
            self.current_connection = 0
            self.wizard.move_target.position = self.path[0].fromNode.position

        else:
            self.wizard.move_target.position = self.wizard.path_graph.nodes[
                self.wizard.base.target_node_index].position


class WizardStateAttacking_TeamA(State):

    def __init__(self, wizard):

        State.__init__(self, "attacking")
        self.wizard = wizard

    def do_actions(self):

        opponent_distance = (self.wizard.position -
                             self.wizard.target.position).length()

        # opponent within range
        is_knight_nearby = self.wizard.world.get_all_nearby_opponents(self.wizard)
        if opponent_distance <= self.wizard.min_target_distance:

            enemy_base = self.wizard.world.enemy_base(self.wizard)

            #nearest_opponent = self.wizard.world.get_nearest_opponent(self.wizard)

            enemy_spawn_pos = enemy_base.spawn_position
            enemy_spawn_pos_distance = (self.wizard.position - enemy_spawn_pos).length()

            self.wizard.velocity = Vector2(0, 0)
            if self.wizard.current_ranged_cooldown <= 0:

                if enemy_spawn_pos_distance <= 250 and is_knight_nearby == 1: #if near base, move towards the enemy spawn point, once enemy spawn point is in range, fire at it
                    self.wizard.velocity = enemy_spawn_pos - self.wizard.position
                    if self.wizard.velocity.length() > 0:
                        self.wizard.velocity.normalize_ip()
                        self.wizard.velocity *= self.wizard.maxSpeed

                if enemy_spawn_pos_distance <= self.wizard.min_target_distance:  
                        self.wizard.ranged_attack(enemy_spawn_pos, self.wizard.explosion_image)

                else:
                    self.wizard.ranged_attack(
                        self.wizard.target.position, self.wizard.explosion_image)

        else:
            self.wizard.velocity = self.wizard.target.position - self.wizard.position
            if self.wizard.velocity.length() > 0:
                self.wizard.velocity.normalize_ip()
                self.wizard.velocity *= self.wizard.maxSpeed

    def check_conditions(self):

        # target is gone
        if self.wizard.world.get(self.wizard.target.id) is None or self.wizard.target.ko:
            self.wizard.target = None
            return "seeking"

        nearest_opponent = self.wizard.world.get_nearest_opponent(self.wizard)
        opponent_distance = (self.wizard.position -
                             nearest_opponent.position).length()

        #if nearest_opponent.max_hp == 400 or nearest_opponent.max_hp == 100 and opponent_distance <= self.wizard.min_target_distance:
        if nearest_opponent.melee_damage > 0 and opponent_distance <= self.wizard.min_target_distance:
            if self.wizard.current_ranged_cooldown == self.wizard.ranged_cooldown:
                self.wizard.target = nearest_opponent
                #return "kiting"

        return None

    def entry_actions(self):

        return None


class WizardStateKiting_TeamA(State):
    def __init__(self, wizard):

        State.__init__(self, "kiting")
        self.wizard = wizard

    def do_actions(self):

        self.wizard.velocity = self.wizard.position - self.wizard.target.position
        if self.wizard.velocity.length() > 0:
            self.wizard.velocity.normalize_ip()
            self.wizard.velocity *= self.wizard.maxSpeed

    def check_conditions(self):
        # larger number, longer it takes for wizard to escape kiting state and go back to attacking. 1.75 just nice?
        if self.wizard.current_ranged_cooldown <= self.wizard.ranged_cooldown / 1.5:
            return "attacking"

    def entry_actions(self):

        return None


class WizardStateKO_TeamA(State):

    def __init__(self, wizard):

        State.__init__(self, "ko")
        self.wizard = wizard

    def do_actions(self):

        return None

    def check_conditions(self):

        # respawned
        if self.wizard.current_respawn_time <= 0:
            self.wizard.current_respawn_time = self.wizard.respawn_time
            self.wizard.ko = False
            self.wizard.path_graph = self.wizard.world.paths[randint(
                0, len(self.wizard.world.paths)-1)]
            return "seeking"

        return None

    def entry_actions(self):

        self.wizard.current_hp = self.wizard.max_hp
        self.wizard.position = Vector2(self.wizard.base.spawn_position)
        self.wizard.velocity = Vector2(0, 0)
        self.wizard.target = None

        return None
