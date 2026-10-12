"""Evaluador balístico para proyectiles, rebotes elásticos y colisión contra cápsulas."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class BallProjectile:
    """Proyectil autoritativo simulado en el servidor."""

    ball_id: int
    thrower_id: int
    pos_x: float
    pos_y: float
    pos_z: float
    vel_x: float
    vel_y: float
    vel_z: float
    radius: float = 0.25
    bounces: int = 0
    max_bounces: int = 3
    is_active: bool = True
    alive_time: float = 0.0
    max_lifetime: float = 8.0


class BallisticHitEvaluator:
    """Simula cinemática parabólica y registra impactos balísticos en tiempo real."""

    def __init__(
        self,
        gravity: float = 9.8,
        restitution: float = 0.70,
        floor_y: float = 401.80,
        capsule_radius: float = 0.45,
        capsule_height: float = 1.80,
    ) -> None:
        self.gravity = gravity
        self.restitution = restitution
        self.floor_y = floor_y
        self.capsule_radius = capsule_radius
        self.capsule_height = capsule_height
        self._next_ball_id: int = 1
        self.balls: list[BallProjectile] = []

    def spawn_ball(
        self,
        thrower_id: int,
        origin: tuple[float, float, float],
        direction: tuple[float, float, float],
        speed: float = 18.0,
    ) -> BallProjectile:
        """Instancia una nueva pelota balística."""
        # Normalizar vector de dirección
        dx, dy, dz = direction
        mag = math.sqrt(dx * dx + dy * dy + dz * dz)
        if mag > 0.0001:
            dx /= mag
            dy /= mag
            dz /= mag
        else:
            dx, dy, dz = (0.0, 0.0, 1.0)

        ball = BallProjectile(
            ball_id=self._next_ball_id,
            thrower_id=thrower_id,
            pos_x=origin[0],
            pos_y=origin[1] + 1.2, # Altura de lanzamiento desde el pecho
            pos_z=origin[2],
            vel_x=dx * speed,
            vel_y=dy * speed + 1.5, # Ligera elevación parabólica
            vel_z=dz * speed,
        )
        self._next_ball_id += 1
        self.balls.append(ball)
        return ball

    def update(
        self,
        dt: float,
        targets: list[tuple[int, float, float, float]], # (entity_id, pos_x, pos_y, pos_z)
    ) -> list[tuple[int, BallProjectile]]:
        """Avanza la simulación balística y detecta impactos en el tick actual.

        Retorna una lista de tuplas `(hit_entity_id, ball)`.
        """
        hits: list[tuple[int, BallProjectile]] = []

        for ball in self.balls:
            if not ball.is_active:
                continue

            ball.alive_time += dt
            if ball.alive_time >= ball.max_lifetime:
                ball.is_active = False
                continue

            # Integración de movimiento
            ball.pos_x += ball.vel_x * dt
            ball.pos_y += ball.vel_y * dt
            ball.pos_z += ball.vel_z * dt
            ball.vel_y -= self.gravity * dt

            # Rebote con el suelo
            if ball.pos_y <= self.floor_y + ball.radius:
                ball.pos_y = self.floor_y + ball.radius
                ball.vel_y = -ball.vel_y * self.restitution
                ball.vel_x *= self.restitution
                ball.vel_z *= self.restitution
                ball.bounces += 1
                if ball.bounces > ball.max_bounces or abs(ball.vel_y) < 0.5:
                    ball.is_active = False
                    continue

            # Verificación de colisión contra cada cápsula de participante
            for t_id, tx, ty, tz in targets:
                # No impactar al lanzador inmediatamente si la pelota va despegando
                if t_id == ball.thrower_id and ball.alive_time < 0.25:
                    continue

                if self._check_sphere_capsule_collision(ball, tx, ty, tz):
                    ball.is_active = False
                    hits.append((t_id, ball))
                    break

        # Limpiar pelotas inactivas
        self.balls = [b for b in self.balls if b.is_active]
        return hits

    def _check_sphere_capsule_collision(
        self,
        ball: BallProjectile,
        cap_x: float,
        cap_y: float,
        cap_z: float,
    ) -> bool:
        """Determina la distancia euclidiana entre una esfera y una cápsula vertical."""
        # Punto más cercano en el segmento vertical de la cápsula [cap_y, cap_y + capsule_height]
        clamped_y = max(cap_y, min(ball.pos_y, cap_y + self.capsule_height))

        dx = ball.pos_x - cap_x
        dy = ball.pos_y - clamped_y
        dz = ball.pos_z - cap_z
        dist_sq = dx * dx + dy * dy + dz * dz

        total_r = ball.radius + self.capsule_radius
        return dist_sq <= (total_r * total_r)
