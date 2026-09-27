Tecate Game Protocol — TKT/1

1. Propósito

TKT/1 es un protocolo de comunicación multijugador ligero, orientado a videojuegos con mundo compartido y clientes autoritativos en representación, pero con un servidor central encargado de mantener y distribuir el estado compartido.

El protocolo está diseñado para:

* comunicación cliente-servidor mediante UDP;
* sincronización de jugadores;
* sincronización de entidades móviles o interactuables;
* propagación de eventos;
* chat y comunicación de jugadores;
* telemetría;
* presencia y sesiones;
* persistencia opcional de estado;
* interest management espacial;
* evolución independiente del cliente y servidor;
* incorporación de nuevos tipos de entidades y propiedades sin modificar necesariamente el núcleo del servidor.

El servidor no contiene ni necesita contener el mapa estático del videojuego. Cada cliente posee localmente el mundo necesario para renderizarlo.

El servidor mantiene exclusivamente información dinámica y compartida.

⸻

2. Principio arquitectónico

La arquitectura fundamental es:

                         INTERNET
                            │
                            │ UDP
                            ▼
              api.tecate.bonsanbec.dev
                            │
                    ┌───────┴───────┐
                    │  TKT Server   │
                    │               │
                    │ Sessions      │
                    │ Entities      │
                    │ Events        │
                    │ Chat          │
                    │ Telemetry     │
                    │ Persistence   │
                    └───────┬───────┘
                            │
                ┌───────────┼───────────┐
                │           │           │
             Client A    Client B    Client C
                │           │           │
              Godot       Godot       Godot
                │           │           │
             World A     World B     World C

El mundo estático es responsabilidad exclusiva del cliente.

El servidor no debe depender de:

* Godot;
* escenas .tscn;
* nodos Godot;
* meshes;
* texturas;
* shaders;
* modelos 3D;
* archivos del mapa;
* recursos gráficos;
* estructura interna del proyecto del videojuego.

El servidor solamente trabaja con datos abstractos.

⸻

3. Transporte

El transporte primario de TKT/1 es UDP.

Endpoint público:

api.tecate.bonsanbec.dev

Puerto de juego recomendado para V1:

UDP/52665

Por tanto:

api.tecate.bonsanbec.dev:52665/UDP

El puerto es configurable y no forma parte de la semántica del protocolo

⸻

4. Objetivos de UDP

UDP se utiliza porque una parte importante del estado del juego es temporal.

Por ejemplo, perder:

Player 17 estaba en X=100

no requiere retransmitir el paquete si posteriormente se recibe:

Player 17 está en X=103

Por ello existen dos categorías de transmisión:

Unreliable

Utilizada para:

* snapshots;
* posiciones;
* rotaciones;
* velocidad;
* estados transitorios;
* telemetría frecuente.

La pérdida de un paquete no requiere retransmisión.

Reliable

Utilizada para:

* autenticación;
* creación/destrucción de entidades;
* eventos importantes;
* mensajes de chat;
* cambios persistentes;
* confirmaciones;
* acciones cuya pérdida produciría estados divergentes.

La confiabilidad será implementada en la capa de protocolo mediante sequence, ack y retransmisión selectiva, no mediante TCP.

⸻

5. Formato general del paquete

Todos los paquetes TKT/1 comienzan con un encabezado común.

Conceptualmente:

Header
├── magic
├── protocol_version
├── message_type
├── flags
├── session_id
├── sequence
├── acknowledgement
├── timestamp
└── payload_length

Los campos deben utilizar representación binaria compacta y un endianness único definido por la implementación.

La implementación inicial puede utilizar little-endian, siempre que se documente explícitamente y sea uniforme en ambos extremos.

Campos

magic

Identificador fijo que permite distinguir paquetes TKT de tráfico UDP ajeno.

protocol_version

Versión mayor del protocolo.

Para esta especificación:

1

message_type

Identifica el contenido del payload.

flags

Indica propiedades del paquete, incluyendo si pertenece al canal fiable.

session_id

Identifica la sesión de conexión.

sequence

Número monotónico de paquete enviado por el emisor.

acknowledgement

Último paquete recibido del otro extremo.

timestamp

Marca temporal asociada al paquete.

payload_length

Longitud del payload.

⸻

6. Versionado

La versión del protocolo debe ser independiente de la versión del videojuego.

Por ejemplo:

Game 1.0 ─┐
Game 1.1 ─┤
Game 1.2 ─┼── TKT/1
Game 1.3 ─┤
Game 1.4 ─┘

Mientras el contrato de TKT permanezca compatible, el servidor no necesita actualizarse.

El cliente debe enviar su propia versión:

client_version

pero esta no forma parte de la versión del protocolo.

Un cambio incompatible en la semántica del protocolo requiere:

TKT/2

Los cambios compatibles deben implementarse mediante:

* nuevas propiedades;
* nuevos tipos de entidad;
* nuevos eventos;
* campos opcionales;
* extensiones negociadas.

⸻

7. Sesión

Una conexión comienza mediante:

HELLO

El cliente proporciona:

protocol_version
client_version
client_capabilities
authentication_data

El servidor responde:

WELCOME

con:

protocol_version
session_id
player_entity_id
server_tick
server_time
server_capabilities

A partir de WELCOME, el cliente dispone de una sesión válida.

El servidor debe asociar:

session_id
player_entity_id
remote_address
last_seen
client_version

⸻

8. Mensajes principales

TKT/1 define inicialmente los siguientes mensajes:

HELLO
WELCOME
INPUT
SNAPSHOT
EVENT
CHAT
TELEMETRY
PING
PONG
GOODBYE

No todos requieren transmisión fiable.

⸻

9. HELLO

Dirección:

Client → Server

Propósito:

Solicitar establecimiento de una sesión.

Contenido:

protocol_version
client_version
client_capabilities
authentication_data

El servidor puede rechazar la conexión mediante un mensaje de error dentro de la respuesta correspondiente.

⸻

10. WELCOME

Dirección:

Server → Client

Propósito:

Confirmar una sesión válida.

Contenido:

protocol_version
session_id
player_entity_id
server_tick
server_time
server_capabilities

El player_entity_id identifica la entidad correspondiente al jugador conectado.

⸻

11. Entity

La entidad es la abstracción fundamental del mundo dinámico.

Entity
├── id
├── type
├── position
├── rotation
└── properties

id

Identificador numérico único dentro del servidor.

Debe permanecer estable durante toda la existencia de la entidad.

type

Tipo semántico de entidad.

Ejemplos:

player
vehicle
object
npc
item

El protocolo no obliga a una lista cerrada.

El cliente decide cómo representar visualmente cada tipo.

position

Posición tridimensional en el sistema de coordenadas propio del videojuego.

[x, y, z]

El protocolo no asume GPS ni ningún otro sistema geográfico.

La transformación entre el mapa físico y el espacio del juego pertenece al cliente.

rotation

Orientación de la entidad.

Puede representarse inicialmente mediante:

[x, y, z]

o mediante quaternion si el juego lo requiere.

La representación debe quedar fijada por la implementación V1 y no cambiar dinámicamente.

properties

Mapa dinámico de propiedades de la entidad.

Ejemplo:

{
    "velocity": [1.2, 0.0, -3.4],
    "health": 100,
    "animation": "running",
    "vehicle": 381,
    "fuel": 72.5
}

El servidor no necesita conocer semánticamente todas las propiedades.

Esto permite incorporar nuevas características del videojuego sin modificar necesariamente el modelo de entidad.

⸻

1.  Política de propiedades

Cada propiedad puede pertenecer conceptualmente a una política de replicación:

ALWAYS
ON_CHANGE
ON_EVENT
LOCAL_ONLY
SERVER_ONLY

ALWAYS

Se transmite periódicamente.

Adecuado para:

velocity
movement_state

ON_CHANGE

Se transmite cuando cambia.

Adecuado para:

health
fuel
vehicle
equipment

ON_EVENT

Se comunica como parte de un evento.

Adecuado para:

animation_started
object_interacted
weapon_fired

LOCAL_ONLY

Nunca se transmite.

SERVER_ONLY

Nunca se envía al cliente.

Esta política evita que el mapa dinámico de properties se convierta accidentalmente en una fuente de tráfico innecesario.

⸻

13. INPUT

Dirección:

Client → Server

INPUT representa la intención o actividad del jugador.

Ejemplos:

movement
look
jump
interact
action
vehicle_control

El payload puede contener:

input_sequence
client_timestamp
input_state
properties

El servidor no necesita conocer todas las acciones posibles.

Ejemplo conceptual:

{
    "movement": [0.0, 1.0],
    "look": [0.2, -0.1],
    "actions": ["jump"]
}

El formato concreto de las entradas debe mantenerse independiente de la representación visual.

⸻

14. SNAPSHOT

Dirección:

Server → Client

Es el mecanismo principal de sincronización de estado dinámico.

Contiene:

server_tick
timestamp
entities[]

Ejemplo conceptual:

{
    "server_tick": 18342,
    "entities": [
        {
            "id": 17,
            "type": "player",
            "position": [150.2, 65.0, -220.8],
            "rotation": [0.0, 1.57, 0.0],
            "properties": {
                "velocity": [1.2, 0.0, 0.4],
                "state": "walking"
            }
        }
    ]
}

Los snapshots son normalmente unreliable.

El cliente debe interpolar los estados recibidos para evitar movimiento visual entrecortado.

⸻

15. Interpolación

El servidor no necesita transmitir posiciones a la frecuencia del renderizado.

El cliente debe mantener un pequeño buffer de estados recientes y producir una representación visual interpolada.

Por tanto:

Servidor
    │
 snapshots
    │
    ▼
Cliente
    │
 buffer
    │
 interpolación
    ▼
render

Esto permite reducir significativamente el tráfico sin degradar necesariamente la apariencia del movimiento.

⸻

16. EVENT

Los eventos representan acontecimientos discretos.

Ejemplos:

PLAYER_JOIN
PLAYER_LEAVE
ENTITY_CREATE
ENTITY_DESTROY
ENTITY_ACTION
ENTITY_INTERACT
PROPERTY_CHANGED
VEHICLE_ENTER
VEHICLE_EXIT
OBJECT_PICKUP
OBJECT_DROP
SYSTEM_MESSAGE

Un evento contiene conceptualmente:

event_id
event_type
entity_id
timestamp
payload

Los eventos importantes utilizan transmisión fiable.

Los eventos son especialmente adecuados para información que no tiene sentido retransmitir continuamente.

⸻

17. Creación y destrucción de entidades

Cuando una entidad entra en el área de interés de un cliente:

ENTITY_CREATE

Cuando deja de existir:

ENTITY_DESTROY

Cuando simplemente deja de estar dentro del área de interés, no necesariamente debe destruirse globalmente: el cliente puede eliminar su representación local.

Esto permite separar:

existencia global

de:

existencia conocida por un cliente

⸻

18. Interest Management

El servidor debe poder dividir espacialmente las entidades.

La implementación inicial puede utilizar una cuadrícula:

cell_x = floor(position.x / CELL_SIZE)
cell_z = floor(position.z / CELL_SIZE)

El tamaño de celda es configurable.

Un cliente recibe únicamente entidades dentro de un radio o conjunto de celdas relevantes.

Por ejemplo:

        ┌───┬───┬───┐
        │   │   │   │
        ├───┼───┼───┤
        │   │ P │   │
        ├───┼───┼───┤
        │   │   │   │
        └───┴───┴───┘

El servidor no debe transmitir a un jugador entidades que se encuentren fuera de su área de interés salvo que una mecánica específica lo requiera.

⸻

19. CHAT

El protocolo incluye comunicación textual independiente de las entidades.

Mensaje:

CHAT

Contenido mínimo:

sender_entity_id
channel
message
timestamp

Canales posibles:

global
local
private
system

El protocolo no obliga a una interfaz determinada.

El servidor debe poder aplicar:

* longitud máxima;
* rate limiting;
* sanitización;
* mute;
* permisos;
* moderación.

El contenido del chat no debe formar parte de properties.

⸻

20. TELEMETRY

El cliente puede enviar telemetría al servidor.

Ejemplos:

fps
ping
position
velocity
client_time
packet_loss
render_state

La telemetría debe considerarse información diagnóstica, no necesariamente estado de juego.

Por defecto:

Client → Server

y puede ser unreliable.

El servidor puede utilizarla para:

* diagnóstico;
* estadísticas;
* administración;
* detección de problemas de conectividad;
* métricas de sesión.

No debe depender de ella para mantener la simulación.

⸻

21. PING / PONG

El servidor y cliente pueden intercambiar:

PING
PONG

para determinar:

latency
last_seen
connection_alive

El servidor debe poder eliminar sesiones que permanezcan sin comunicación durante un timeout configurable.

⸻

22. GOODBYE

Permite terminar una sesión explícitamente.

Client → Server
GOODBYE

El servidor libera:

session
temporary entity state
interest registrations
network resources

y genera el correspondiente evento de salida para otros clientes.

⸻

23. Autoridad

TKT/1 adopta una arquitectura parcialmente autoritativa.

El cliente es responsable de:

* representación;
* renderizado;
* animaciones;
* predicción;
* interpolación;
* mundo estático;
* presentación.

El servidor es responsable de:

* identidad;
* sesiones;
* existencia global de entidades;
* distribución del estado;
* eventos;
* permisos;
* persistencia;
* validaciones básicas;
* reglas que deban ser compartidas entre jugadores.

La simulación completa del movimiento puede comenzar siendo sencilla y evolucionar posteriormente hacia un modelo completamente autoritativo.

TKT/1 no exige que la física del videojuego se ejecute en el VPS.

⸻

24. Persistencia

La persistencia es independiente del transporte.

El servidor puede conservar:

player data
entity data
object state
world modifications
inventory
statistics
configuration

El mundo estático no necesita almacenarse en el servidor.

Las modificaciones persistentes deben representarse como datos abstractos, no como archivos completos del mundo del cliente.

⸻

25. Estado efímero frente a persistente

El servidor debe distinguir:

EPHEMERAL

de:

PERSISTENT

Ejemplo efímero:

position
velocity
ping
current animation

Ejemplo persistente:

inventory
owned object
vehicle state
player statistics
world object

La pérdida del estado efímero por reinicio del servidor no constituye necesariamente corrupción del mundo.

⸻

26. Seguridad y autenticación

TKT/1 debe permitir autenticación antes de aceptar una sesión de juego.

El mecanismo concreto de autenticación puede implementarse mediante:

authentication token

emitido por una API HTTP/HTTPS independiente.

Una arquitectura posible es:

HTTPS
api.tecate.bonsanbec.dev
        │
        └── autenticación / administración
UDP
api.tecate.bonsanbec.dev:52665
        │
        └── juego

La autenticación debe producir un token de corta duración o credencial equivalente.

El servidor nunca debe confiar en un player_id enviado arbitrariamente por el cliente.

⸻

27. Rate limiting

El servidor debe limitar como mínimo:

HELLO
CHAT
EVENT
INPUT

para impedir abuso accidental o deliberado.

Los snapshots enviados por el servidor deben estar controlados por una frecuencia máxima configurable.

⸻

28. Límites

TKT/1 debe establecer límites configurables para:

maximum packet size
maximum entities per snapshot
maximum properties per entity
maximum property size
maximum chat message length
maximum event payload
maximum entities per client
maximum packets per second

El protocolo debe evitar fragmentar datagramas UDP siempre que sea posible.

La implementación debe mantener el tamaño de los paquetes suficientemente por debajo del MTU práctico de Internet para reducir fragmentación.

⸻

29. Compatibilidad futura

Los clientes deben ignorar campos opcionales que no reconozcan cuando sea seguro hacerlo.

Los tipos desconocidos deben rechazarse de manera controlada, no provocar la terminación abrupta de la sesión.

Un servidor TKT/1 puede incorporar posteriormente:

NPC
vehicle
projectile
item
construction
trade
mission
inventory

sin cambiar necesariamente el modelo fundamental.

⸻

30. Principio de extensibilidad

La extensión preferida es:

nuevo type
nuevo event_type
nueva property

y no:

nuevo protocolo

siempre que no cambie la semántica fundamental del transporte o de la sincronización.

Por ejemplo, agregar:

type = drone

no requiere TKT/2.

Agregar:

properties = {
    "battery": 84.2,
    "altitude_mode": "auto"
}

tampoco requiere TKT/2.

Pero modificar radicalmente la semántica de SNAPSHOT o del sistema de sesiones sí podría justificar una nueva versión mayor.

⸻

31. Sistema de coordenadas

TKT no impone un sistema geográfico.

Todas las posiciones transmitidas corresponden al espacio de coordenadas del videojuego:

position = [x, y, z]

El cliente es responsable de conocer la relación entre ese espacio y su mundo.

Esto permite que el servidor permanezca completamente independiente del origen de los datos del mapa.

En el caso del proyecto Tecate, el mundo utiliza una representación espacial coherente y a escala 1:1, pero esa característica pertenece al juego y no al protocolo. El modelo espacial existente distingue explícitamente entre el sistema geográfico, el cartesiano local y el espacio del engine.

Por tanto, TKT debe permanecer agnóstico respecto de todos ellos.

⸻

32. Separación entre mundo y estado dinámico

El servidor no transmite:

terrain
buildings
roads
meshes
textures
materials
map tiles
GLB
scenes

El servidor transmite:

players
entities
positions
rotations
properties
events
chat
telemetry
session state

Esta separación es una propiedad fundamental de TKT/1.

⸻

33. Modelo conceptual completo

                    TKT/1
                      │
        ┌─────────────┼─────────────┐
        │             │             │
     SESSION       ENTITY         EVENTS
        │             │             │
   authentication   player       interaction
   connection       vehicle      spawn
   presence         object       destroy
   ping             NPC          action
        │             │
        └──────┬──────┘
               │
          COMMUNICATION
               │
        ┌──────┴──────┐
        │             │
      CHAT        TELEMETRY

El servidor mantiene la realidad compartida; el cliente la representa.

⸻

34. Flujo de conexión

Client
  │
  │ HELLO
  ▼
Server
  │
  │ WELCOME
  ▼
Client
  │
  │ INPUT
  ├──────────────────►
  │
  │                 Server
  │                   │
  │                   │ actualiza estado
  │                   │
  │ SNAPSHOT           │
  ◄───────────────────┤
  │
  │ EVENT
  ◄───────────────────┤
  │
  │ CHAT
  ◄───────────────────┤

⸻

35. Primera implementación

TKT/1 no debe implementarse completo de una sola vez.

El primer milestone debe limitarse a:

HELLO
WELCOME
INPUT
SNAPSHOT
PING
PONG
GOODBYE

y únicamente:

Entity.type = player

con:

position
rotation
properties.velocity

El objetivo inicial es demostrar:

Godot A
    │
    ▼
UDP
    │
    ▼
TKT Server
    │
    ▼
UDP
    │
    ▼
Godot B

y que A puede observar la entidad dinámica de B dentro del mismo mundo local.

Una vez validado esto se incorporan, en este orden aproximado:

1. entidades genéricas
2. eventos
3. creación/destrucción
4. interest management
5. chat
6. telemetría
7. autenticación
8. persistencia
9. validación autoritativa
10. optimización

⸻

36. Principio rector de TKT/1

El servidor no debe intentar convertirse en una segunda copia del videojuego.

Debe ser una autoridad ligera sobre el estado compartido.

El cliente debe seguir siendo dueño de:

mundo
renderizado
assets
escenas
presentación
interpolación
predicción

El servidor debe ser dueño de:

sesiones
identidad
entidades
estado compartido
eventos
comunicación
telemetría
persistencia

La frontera entre ambos debe mantenerse explícita y estable.

El objetivo final es que una actualización importante del videojuego pueda modificar su representación, lógica interna, mapa o assets sin exigir simultáneamente una actualización del servidor, salvo que dicha actualización cambie el contrato TKT o introduzca una mecánica que requiera lógica server-side.