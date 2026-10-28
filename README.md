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

`roblox/GlassMall.rbxlx` is the mall as a Roblox place, built from the same traced floor plans (3.5 studs per metre), set in **Glass City**, a drivable city of about 60,000 parts where every floor of every building has an inside. To open it, double-click the file to open it in Roblox Studio and press **Play** to try it.

**The mall:**
- **Getting around:** automatic sliding doors on the court and at the roof terrace. Escalators by the atrium carry you up, and a panoramic glass lift behind a glass shaft stops at every floor.
- **Each floor:** shops on every floor, a food court with seats on 2F, an arcade on 3F, and two cinemas with stepped seating and screens on 4F, plus a planted roof terrace.
- **Shops:** every unit is fitted out for what it sells: racks and mannequins at LOOM, a shoe wall at Sole Story, books, gadgets, flowers, toys, beauty counters, a sports shop and a brick store, and four food-court stalls with kitchens and menus.
- **Life:** shoppers walk in from the street (with walking animations), visit a few places and leave; a security guard, an information desk and kiosk sellers work the ground floor.

**The city round it** (about 830 × 1,140 m):
- **Roads:** a ring highway with a median and lamp posts, a grid of avenues and streets, and the boulevard past the mall running corner to corner. AI traffic loops the ring and runs the boulevard, two avenues and a street, keeping left as in Bengaluru.
- **Districts:** suburbs of houses with driveways and gardens, midtown offices, downtown towers round a plaza with a fountain and an LED screen, uptown apartments with roof gardens, and the mall car park.
- **Inside every building:**
  - **Houses (72):** furnished living rooms, kitchens and bedrooms, stairs to a second floor in the two-storey ones, doors that swing open as you walk up, and a back garden with a pool, trampoline, barbecue, hot tub, swings, vegetable beds or a shed.
  - **Houses** also have a bathroom (shower, toilet and basin), and some have people at home.
  - **Midtown offices (12):** each has a business on the ground floor, from a café, bank, gym, gallery, bookshop and bowling alley to an arcade, clinic and pet shop. The lift stops at **every** floor, and each floor is a different firm (67 in all): a law firm with a library and boardroom, a startup with ping-pong and bean bags, a game studio, a design studio with drafting tables, a yoga studio, a recording studio, a data centre, a school, a photo studio and a trading floor, then the rooftop helipad, court, pool, bar, garden or putting green.
  - **Uptown apartments (11):** a lobby with a concierge and mailboxes, then a corridor and two furnished flats on every floor (164 flats: living room, kitchen, dining table, bedroom or kids' bunk room, and a bathroom), a penthouse and a roof garden with a pergola, barbecue and hot tub.
  - **Downtown towers (15) and the Glass Spire:** a double-height lobby (one is a car showroom with turntables), floors let into the glass tiers on the way up (45 in all: a grand hotel with guest rooms, a trading floor, a sky gym, a spa, a library, a kids' club, a data centre, a game studio, residences and more, each with a second theme behind the lift), and a glass sky lounge at the top: a sky bar, observatory, sky garden, club with a DJ and dancers, sky dining with a pianist, infinity pool or sky cinema. The 232 m Glass Spire stops at nine floors, with two lounges and a glass-floored skywalk.
  - **GLASSTOP Mart:** the fuel station's 24/7 shop, with aisles, fridges, a slushie machine and a cashier.
- **Central Park:** a lake with rowing boats that float, a jetty, paths, benches, a gazebo and a playground.
- **VAYU Hotel:** the VAYU project's 5-star hotel, imported from its model file (`roblox/data/vayu_model.json`), with sliding doors into the lobby and a portal up to the sky pool.
- **Stunt park:** a 16 m mega ramp, two jumps, a quarter pipe, knock-over cones, a drift circle and the GLASSTOP FUEL station.
- **Glass Bay:** a boardwalk with palms, beach umbrellas, a lifeguard tower and a pier into the sea, plus grassy hills round the city.

**Playing:**
- **Cars:** hold **E** on any glowing *Get a car* pad for your own car, or press **E** by any of the 36 parked cars. Drive with W/A/S/D and press Space to get out. Each car is a physics car on hinge motors, steered by servos, with a speedometer and headlights at night. Cars that roll over are put back on their wheels.
- **Lifts:** 39 lifts stopping at 289 floors. Press **E** at a landing to call one; step in and pick a floor on the panel that appears (two columns of buttons, scrolling when a building is tall). The car eases away and slows into each floor smoothly, carries you with it, chimes on arrival, plays lift music and shows the floor on indicators inside and on every landing. Each player's screen draws the car from a shared timetable, so the ride doesn't stutter.
- **Travel and the map:** the Travel button jumps to 14 places. **M** (or the Map button) opens a map of the whole city, with every road, district, building and house and an arrow for you; click a gold pin to go there.
- **Explorer passport:** 400 places to find: every shop, office floor, pair of flats, tower floor, sky lounge, house and landmark. Stand somewhere new for a moment and it's stamped, for 3 coins. **P** (or the Passport button) opens the book, chapter by chapter. Your stamps are saved between visits, and "Places" on the leaderboard shows how many you have.
- **Coins:** 215 gold coins on roads, ramps, rooftops, the pier and inside the buildings. Collect them on foot or by car; your total is saved between visits.
- **Free food and things to hold:** press **E** at any of 41 counters for coffee, filter kaapi, masala dosa, noodles, gelato, popcorn, pizza, bubble tea, candy floss, coconut water, mocktails, juice, a book, a bouquet or a balloon. Click to eat or drink it.
- **Arcade:** 95 glowing screens (the mall's 3F arcade, Pixel Arcade, the game studios, the console shop) play Coin Catch, Glass Dash or Memory Lights, with mouse, keys or touch. A good score wins up to 15 coins.
- **Cinemas:** the 4F cinemas and the sky cinemas play two short animated films, *Monsoon Skies* and *The Last Metro Home*, with music.
- **People:** about 300 people work and live in the city: baristas, cooks, receptionists, teachers, a DJ and dancers, lifeguards, residents. They appear as you come near; press **E** to say hello and get a tip.
- **Sound:** music where it belongs (bossa nova in cafés, jazz in the sky bars, the club, lift music) and the city around you: traffic, birds by day and crickets at night, waves and gulls on the beach, wind high up, the mall's hum. The Sound button mutes it.
- **Atmosphere:** a loading screen, a 16-minute day–night cycle with street lights and lit windows, clouds, monsoon rain now and then (with thunder, and no rain indoors), fireworks over Glass Bay every night, fireflies in Central Park, steam over the food stalls, smoke from chimneys and a working fountain. A label at the top shows your mall floor, building and floor, or city district.

To rebuild the place after changing `roblox/build_place.py` or `roblox/scripts/*.lua`:

```bash
python3 roblox/build_place.py
```

It needs `numpy`.

*Concept visualisation for a student design project, not for construction.*
