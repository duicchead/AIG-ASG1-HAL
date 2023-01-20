import pygame

from random import randint, random
from Graph import *

from Character import *
from State import *

class Knight_TeamA(Character):

    def __init__(self, world, image, base, position):

        Character.__init__(self, world, "knight", image)

        self.base = base
        self.position = position
        self.move_target = GameEntity(world, "knight_move_target", None)
        self.target = None
        self.level = 0

        self.maxSpeed = 80
        self.min_target_distance = 100
        self.melee_damage = 20
        self.melee_cooldown = 2.

        seeking_state = KnightStateSeeking_TeamA(self)
        attacking_state = KnightStateAttacking_TeamA(self)
        ko_state = KnightStateKO_TeamA(self)

        self.brain.add_state(seeking_state)
        self.brain.add_state(attacking_state)
        self.brain.add_state(ko_state)

        self.brain.set_state("seeking")
        

    def render(self, surface):

        Character.render(self, surface)


    def process(self, time_passed):
        
        Character.process(self, time_passed)

        level_up_stats = ["hp", "speed", "melee damage", "melee cooldown", "healing"]
        if self.can_level_up():
            self.level += 1
            #choice = randint(0, len(level_up_stats) - 1)
            choice = 4
            self.level_up(level_up_stats[choice])

   


class KnightStateSeeking_TeamA(State):

    def __init__(self, knight):

        State.__init__(self, "seeking")
        self.knight = knight

        self.knight.path_graph = self.knight.world.paths[randint(0, len(self.knight.world.paths)-1)]


    def do_actions(self):

        self.knight.velocity = self.knight.move_target.position - self.knight.position
        if self.knight.velocity.length() > 0:
            self.knight.velocity.normalize_ip();
            self.knight.velocity *= self.knight.maxSpeed


    def check_conditions(self):

        # check if opponent is in range
        nearest_opponent = self.knight.world.get_nearest_opponent(self.knight)
        if nearest_opponent is not None:
            opponent_distance = (self.knight.position - nearest_opponent.position).length()

            if self.knight.current_hp < 350 and opponent_distance >= 150:
                self.knight.heal()

            if opponent_distance <= self.knight.min_target_distance:
                self.knight.target = nearest_opponent
                return "attacking"
        
        if (self.knight.position - self.knight.move_target.position).length() < 8:

            # continue on path
            if self.current_connection < self.path_length:
                self.knight.move_target.position = self.path[self.current_connection].toNode.position
                self.current_connection += 1
            
        return None


    def entry_actions(self):

        nearest_node = self.knight.path_graph.get_nearest_node(self.knight.position)

        self.path = pathFindAStar(self.knight.path_graph, \
                                  nearest_node, \
                                  self.knight.path_graph.nodes[self.knight.base.target_node_index])

        
        self.path_length = len(self.path)

        if (self.path_length > 0):
            self.current_connection = 0
            self.knight.move_target.position = self.path[0].fromNode.position

        else:
            self.knight.move_target.position = self.knight.path_graph.nodes[self.knight.base.target_node_index].position


class KnightStateAttacking_TeamA(State):

    def __init__(self, knight):

        State.__init__(self, "attacking")
        self.knight = knight

    def do_actions(self):
        num_of_nearby_heroes = self.knight.world.get_all_nearby_heroes(self.knight)
        is_wizard_near = self.knight.world.is_my_wizard_nearby(self.knight)
        enemy_base = self.knight.world.enemy_base(self.knight)
        enemy_spawn_pos = enemy_base.spawn_position
        enemy_spawn_pos_distance = (self.knight.position - enemy_spawn_pos).length()


        if enemy_spawn_pos_distance <= 250 and self.knight.level >= 3 and is_wizard_near >= 1: #if near base, move towards the enemy spawn point, once enemy spawn point is in range, fire at it
            self.knight.velocity = enemy_spawn_pos - self.knight.position
            if self.knight.velocity.length() > 0:
                self.knight.velocity.normalize_ip()
                self.knight.velocity *= self.knight.maxSpeed
        
        else:

            # colliding with target
            if pygame.sprite.collide_rect(self.knight, self.knight.target):
                self.knight.velocity = Vector2(0, 0)
                self.knight.melee_attack(self.knight.target)

            else:
                self.knight.velocity = self.knight.target.position - self.knight.position
                if self.knight.velocity.length() > 0:
                    self.knight.velocity.normalize_ip();
                    self.knight.velocity *= self.knight.maxSpeed


    def check_conditions(self):
        num_of_nearby_opponents = self.knight.world.get_all_nearby_opponents(self.knight)
        num_of_nearby_heroes = self.knight.world.get_all_nearby_heroes(self.knight)
        
        if self.knight.current_hp < 270 and self.knight.level >= 3 and num_of_nearby_heroes >= 1:
            self.knight.heal()

        if self.knight.current_hp < 350 and num_of_nearby_opponents == 0: #if no enemies nearby, jus heal
            self.knight.heal()

        # target is gone
        if self.knight.world.get(self.knight.target.id) is None or self.knight.target.ko:
            self.knight.target = None
            return "seeking"
            
        return None

    def entry_actions(self):

        return None


class KnightStateKO_TeamA(State):

    def __init__(self, knight):

        State.__init__(self, "ko")
        self.knight = knight

    def do_actions(self):

        return None


    def check_conditions(self):

        # respawned
        if self.knight.current_respawn_time <= 0:
            self.knight.current_respawn_time = self.knight.respawn_time
            self.knight.ko = False
            self.knight.path_graph = self.knight.world.paths[randint(0, len(self.knight.world.paths)-1)]
            return "seeking"
            
        return None

    def entry_actions(self):

        self.knight.current_hp = self.knight.max_hp
        self.knight.position = Vector2(self.knight.base.spawn_position)
        self.knight.velocity = Vector2(0, 0)
        self.knight.target = None

        return None
