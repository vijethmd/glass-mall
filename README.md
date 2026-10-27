# Glass Mall

A 3D glass model of a G+4 shopping mall with four basements, traced from the floor plans of an Architectural Design V project (plans by Harsha J.V, K.S. School of Architecture). It runs in the browser with three.js.

![Golden hour from the main road](renders/hero-golden.jpg)

| | |
|---|---|
| ![Night](renders/hero-night.jpg) | ![Glass model](renders/hero-glass-model.jpg) |
| ![Exploded floors](renders/hero-exploded.jpg) | ![Street view](renders/hero-entrance.jpg) |

## What's in the model

Every floor outline was traced from the drawings at 11.7 px per metre, using the 24.4 m dimension on the ground-floor anchor store as the reference.

| Level | Height | Use (from the plans) | Plate |
|---|---|---|---|
| 4F | +15.0, 6 m | Two multiplexes, 1,200 m² each | 3,319 m² |
| 3F | +12.0, 3 m | Arcade 1,200 m², medium and large stores | 3,394 m² |
| 2F | +9.0, 3 m | Food court, small to large stores | 3,136 m² |
| 1F | +6.0, 3 m | Anchor stores 1,150 and 900 m² | 2,905 m² |
| GF | ±0.0, 6 m | Anchor store 800 m², atrium, entrance court | 2,146 m² |
| B1–B4 | −4 to −16 m | Parking | 3,460 m² each |

- **Atrium:** an 8 × 8 m square turned 39°, with escalators on two sides. It runs through every floor to a glazed skylight.
- **Cantilevers:** the upper floors cantilever over the entrance court on columns, and the east multiplex projects past the diagonal site edge.
- **Added for the visualisation, not in the plans:** curtain-wall details, fritted glass on the multiplexes, an LED media screen, roof solar panels, a roof terrace, interior fittings, people, landscape and the surrounding city.

## Run it

```bash
python3 serve.py
```

Then open http://localhost:8766. `index.html` is a page fragment (no `<html>` or `<head>`); `serve.py` adds the wrapper when it serves it.

**Controls:**
- **Mode:** switch between the realistic glass building and the glass model.
- **Light:** day, golden hour or night.
- **Floors:** explode the floors apart, or click a level to cut the building down to it.

## Roblox game

**Play it:** [Glass Mall on Roblox](https://www.roblox.com/games/98868923375548/Glass-Mall)

Step-by-step publishing instructions are in [`roblox/PUBLISH.md`](roblox/PUBLISH.md).

`roblox/GlassMall.rbxlx` is the mall as a Roblox place, built from the same traced floor plans (3.5 studs per metre), set in **Glass City**, a drivable city of about 10,000 parts. To open it, double-click the file to open it in Roblox Studio and press **Play** to try it.

**The mall:**
- **Getting around:** automatic sliding doors on the court and at the roof terrace. Escalators by the atrium carry you up, and a glass lift by the shops has floor buttons and call buttons on every landing.
- **Each floor:** shops on every floor, a food court with seats on 2F, an arcade on 3F, and two cinemas with stepped seating and screens on 4F, plus a planted roof terrace.
- **Life:** shoppers walk in from the street, visit a few places and leave.

**The city round it** (about 830 × 1,140 m):
- **Roads:** a ring highway with a median and lamp posts, a grid of avenues and streets, and the boulevard past the mall running corner to corner. AI traffic loops the ring and runs the boulevard, two avenues and a street, keeping left as in Bengaluru.
- **Districts:** suburbs of houses with driveways and gardens, midtown offices, downtown towers round a plaza with a fountain and an LED screen, uptown apartments with roof gardens, and the mall car park.
- **Central Park:** a lake with rowing boats that float, a jetty, paths, benches, a gazebo and a playground.
- **VAYU Hotel:** the VAYU project's 5-star hotel, imported from its model file (`roblox/data/vayu_model.json`), with sliding doors into the lobby and a portal up to the sky pool.
- **Stunt park:** a 16 m mega ramp, two jumps, a quarter pipe, knock-over cones, a drift circle and the GLASSTOP FUEL station.
- **Glass Bay:** a boardwalk with palms, beach umbrellas, a lifeguard tower and a pier into the sea, plus grassy hills round the city.

**Playing:**
- **Cars:** hold **E** on any glowing *Get a car* pad for your own car, or press **E** by any of the 36 parked cars. Drive with W/A/S/D and press Space to get out. Each car is a physics car on hinge motors, steered by servos, with a speedometer and headlights at night. Cars that roll over are put back on their wheels.
- **Travel:** the Travel button jumps to 13 places, from the mall to the pier.
- **Coins:** 105 gold coins on roads, ramps, rooftops and the pier. Collect them on foot or by car; your total is on the leaderboard and saved between visits.
- **Atmosphere:** a 16-minute day–night cycle. At dusk the street lights come on and the windows across the city light up. A label at the top shows your mall floor or city district.

To rebuild the place after changing `roblox/build_place.py` or `roblox/scripts/*.lua`:

```bash
python3 roblox/build_place.py
```

It needs `numpy`.

*Concept visualisation for a student design project, not for construction.*
