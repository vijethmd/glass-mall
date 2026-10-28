#!/usr/bin/env python3
"""Build GlassMall.rbxlx: the glass mall, and the city round it, as a Roblox place.

The mall is traced from the same floor plans as ../index.html (page pixels at 200 dpi,
0.0857 m per px). Round it is Glass City: a ring highway, avenues, a boulevard, districts,
the VAYU hotel (data/vayu_model.json), a stunt park and a beach, with drivable cars.
Roblox space: 3.5 studs per metre, X east, Y up, Z south.
Run this, open GlassMall.rbxlx in Roblox Studio, then File > Publish to Roblox.
"""
import json
import math
import random
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "GlassMall.rbxlx"
SCRIPTS = ROOT / "scripts"
S, K = 0.0857, 3.5            # metres per page px, studs per metre
DEG = math.pi / 180
rnd = random.Random(11)


# ------------------------------------------------------------------ plan geometry (metres)
def P(px, py):
    return np.array([(px - 657) * S, (1157 - py) * S])


def area(poly):
    return sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(poly, poly[1:] + poly[:1])) / 2


def ccw(poly):
    poly = [np.array(p, float) for p in poly]
    return poly if area(poly) > 0 else poly[::-1]


def inside(p, poly):
    c = False
    for i in range(len(poly)):
        a, b = poly[i], poly[i - 1]
        if (a[1] > p[1]) != (b[1] > p[1]) and p[0] < (b[0] - a[0]) * (p[1] - a[1]) / (b[1] - a[1]) + a[0]:
            c = not c
    return c


def unit(v):
    return v / np.linalg.norm(v)


PX = {
    "GF": [(657, 337), (1395, 337), (1395, 733), (657, 733)],
    "F1": [(638, 337), (1395, 337), (1395, 897), (948, 897), (638, 808)],
    "F2": [(640, 337), (1395, 337), (1395, 958), (948, 958), (948, 900), (845, 900), (640, 808)],
    "F3": [(657, 337), (1395, 337), (1395, 1157), (660, 812)],
    "F4": [(635, 337), (1395, 337), (1395, 1157), (1010, 980), (1010, 830), (635, 830)],
}
POLY = {k: ccw([P(*p) for p in v]) for k, v in PX.items()}
NORTH, EAST = P(0, 337)[1], P(1395, 0)[0]

AC = P(1145, 491)                                   # atrium centre
A_SIDE = 95 * S
EX = np.array([math.cos(51 * DEG), -math.sin(51 * DEG)])
EY = np.array([-math.sin(51 * DEG), -math.cos(51 * DEG)])
HOLE_HX, HOLE_HY = A_SIDE / 2 + 0.4, A_SIDE / 2 + 1.9


def rect_at(c, hx, hy):
    return ccw([c + EX * a * hx + EY * b * hy for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))])


def hole_pt(ex, ey):
    return AC + EX * ex + EY * ey


HOLE = rect_at(AC, HOLE_HX, HOLE_HY)

LEVELS = [  # id, floor z, storey height, outline, note
    ("GF", 0.0, 6.0, "GF", "Shops, atrium and main entrance"),
    ("1F", 6.0, 3.0, "F1", "Fashion and anchor stores"),
    ("2F", 9.0, 3.0, "F2", "Food court"),
    ("3F", 12.0, 3.0, "F3", "Arcade and games"),
    ("4F", 15.0, 6.0, "F4", "Cinemas and roof terrace"),
]
ROOF_Z = 21.0                                        # underside of the roof slab


def floor_top(i):
    return 0.03 if i == 0 else LEVELS[i][1]


def wall_top(i):
    return ROOF_Z if i == 4 else LEVELS[i][1] + LEVELS[i][2] - 0.35


def ceiling(i):
    return ROOF_Z if i == 4 else LEVELS[i][1] + LEVELS[i][2] - 0.412


# cores (stairs, risers) and the lift shaft, set just behind the glass line
def px_rect(x0, y0, x1, y1):
    p, q = P(x0, y1), P(x1, y0)
    return [p[0], p[1], min(q[0], EAST - 0.3), min(q[1], NORTH - 0.3)]


SHAFT = px_rect(995, 337, 1055, 392)
CORES = [px_rect(*r) for r in ((1225, 337, 1265, 460), (1318, 337, 1395, 452),
                               (1310, 505, 1393, 565), (1350, 565, 1393, 602))]
SHAFT_IN = [SHAFT[0] + 0.25, SHAFT[1] + 0.25, SHAFT[2] - 0.25, SHAFT[3] - 0.25]
SHAFT_HOLE = ccw([np.array(p) for p in ((SHAFT_IN[0], SHAFT_IN[1]), (SHAFT_IN[2], SHAFT_IN[1]),
                                        (SHAFT_IN[2], SHAFT_IN[3]), (SHAFT_IN[0], SHAFT_IN[3]))])

HALL_A = (-1.6, 44.5, 22.0, 69.9)                     # 4F multiplex halls (x0, y0, x1, y1)
HALL_B = (50.0, 7.5, 62.8, 31.0)

xs = [p[0] for p in POLY["F4"] + POLY["F3"]]
ys = [p[1] for p in POLY["F3"]]
CX, CY = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2


def R3(x, y, z):
    """Model metres -> Roblox studs."""
    return np.array([(x - CX) * K, z * K, -(y - CY) * K])


def D3(dx, dy, dz):
    """Model direction -> Roblox direction (a proper rotation)."""
    return np.array([dx, dz, -dy], float)


# ------------------------------------------------------------------ triangulation
def cross2(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def segs_cross(p1, p2, p3, p4):
    d1, d2 = cross2(p3, p4, p1), cross2(p3, p4, p2)
    d3, d4 = cross2(p1, p2, p3), cross2(p1, p2, p4)
    return d1 * d2 < -1e-12 and d3 * d4 < -1e-12


def edges(poly):
    return list(zip(poly, poly[1:] + poly[:1]))


def triangulate(outer, holes=()):
    """Ear clipping; holes are joined to the outline by bridges."""
    ring = ccw(outer)
    hs = sorted(([np.array(p, float) for p in ccw(h)][::-1] for h in holes), key=lambda h: -max(p[0] for p in h))
    for n_h, h in enumerate(hs):
        mi = max(range(len(h)), key=lambda i: h[i][0])
        M = h[mi]
        blockers = edges(ring) + edges(h) + [e for o in hs[n_h + 1:] for e in edges(o)]
        best = None
        for i, V in enumerate(ring):
            if any(segs_cross(M, V, a, b) for a, b in blockers):
                continue
            mid = (M + V) / 2
            if not inside(mid, ring) or inside(mid, h):
                continue
            d = np.linalg.norm(V - M)
            if best is None or d < best[0]:
                best = (d, i)
        i = best[1]
        ring = ring[:i + 1] + [h[(mi + j) % len(h)] for j in range(len(h) + 1)] + [ring[i]] + ring[i + 1:]
    idx, tris = list(range(len(ring))), []
    while len(idx) > 3:
        for k in range(len(idx)):
            ia, ib, ic = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            a, b, c = ring[ia], ring[ib], ring[ic]
            if cross2(a, b, c) <= 1e-9:
                continue
            blocked = False
            for j in idx:
                p = ring[j]
                if j in (ia, ib, ic) or any(np.allclose(p, q) for q in (a, b, c)):
                    continue
                if cross2(a, b, p) >= -1e-9 and cross2(b, c, p) >= -1e-9 and cross2(c, a, p) >= -1e-9:
                    blocked = True
                    break
            if not blocked:
                tris.append((a, b, c))
                idx.pop(k)
                break
        else:
            raise RuntimeError("triangulation stuck")
    tris.append(tuple(ring[j] for j in idx))
    want = abs(area(ccw(outer))) - sum(abs(area(ccw(h))) for h in holes)
    got = sum(abs(cross2(*t)) / 2 for t in tris)
    assert abs(want - got) < 1e-6 * max(1, want), (want, got)
    return tris


def offset(poly, d):
    """Move every edge of a CCW outline inward by d (outward if d < 0)."""
    lines = []
    for a, b in edges(poly):
        u = unit(b - a)
        lines.append((a + np.array([-u[1], u[0]]) * d, u))
    out = []
    for i in range(len(lines)):
        (p1, u1), (p2, u2) = lines[i - 1], lines[i]
        t, _ = np.linalg.solve(np.array([u1, -u2]).T, p2 - p1)
        out.append(p1 + t * u1)
    return out


# ------------------------------------------------------------------ rbxlx writer
MAT = {"SmoothPlastic": 272, "Neon": 288, "Wood": 512, "WoodPlanks": 528, "Marble": 784, "Slate": 800,
       "Concrete": 816, "Granite": 832, "Metal": 1088, "DiamondPlate": 1056, "Grass": 1280,
       "Fabric": 1312, "Asphalt": 1376, "Glass": 1568, "Brick": 848, "Sand": 1296}


class Inst:
    count = 0

    def __init__(self, cls, name, **props):
        Inst.count += 1
        self.ref = "RBX%05X" % Inst.count
        self.cls, self.name, self.props, self.kids = cls, name, props, []


def new(parent, cls, name, **props):
    inst = Inst(cls, name, **props)
    if parent is not None:
        parent.kids.append(inst)
    return inst


def num(v):
    if isinstance(v, (bool, np.bool_)):
        raise TypeError(v)
    if isinstance(v, (int, np.integer)):
        return str(int(v))
    s = "%.4f" % float(v)
    s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def prop_xml(name, t, v):
    if t == "bool":
        return '<bool name="%s">%s</bool>' % (name, "true" if v else "false")
    if t in ("float", "double", "int", "int64", "token"):
        return '<%s name="%s">%s</%s>' % (t, name, num(v), t)
    if t == "string":
        return '<string name="%s">%s</string>' % (name, escape(v))
    if t == "v3":
        return '<Vector3 name="%s"><X>%s</X><Y>%s</Y><Z>%s</Z></Vector3>' % ((name,) + tuple(num(c) for c in v))
    if t == "cf":
        pos, R = v
        vals = [num(c) for c in pos] + [num(R[i, j]) for i in range(3) for j in range(3)]
        tags = ["X", "Y", "Z", "R00", "R01", "R02", "R10", "R11", "R12", "R20", "R21", "R22"]
        return '<CoordinateFrame name="%s">%s</CoordinateFrame>' % (
            name, "".join("<%s>%s</%s>" % (g, x, g) for g, x in zip(tags, vals)))
    if t == "c3u8":
        r, g, b = (int(c) for c in v)
        return '<Color3uint8 name="%s">%d</Color3uint8>' % (name, 0xFF000000 | r << 16 | g << 8 | b)
    if t == "c3":
        return '<Color3 name="%s"><R>%s</R><G>%s</G><B>%s</B></Color3>' % ((name,) + tuple(num(c / 255) for c in v))
    if t == "src":
        assert "]]>" not in v
        return '<ProtectedString name="%s"><![CDATA[%s]]></ProtectedString>' % (name, v)
    if t == "ref":
        return '<Ref name="%s">%s</Ref>' % (name, v.ref)
    raise ValueError(t)


def write_item(inst, out):
    out.append('<Item class="%s" referent="%s"><Properties>' % (inst.cls, inst.ref))
    out.append('<string name="Name">%s</string>' % escape(inst.name))
    out.extend(prop_xml(k, t, v) for k, (t, v) in inst.props.items())
    out.append("</Properties>")
    for kid in inst.kids:
        write_item(kid, out)
    out.append("</Item>")


PARTS = []


def part(parent, name, pos, R, size, color, mat="SmoothPlastic", cls="Part", tr=0.0, refl=0.0,
         collide=True, shadow=True, shape=None, query=True):
    assert abs(np.linalg.det(R) - 1) < 1e-6, R
    props = dict(Anchored=("bool", True), CFrame=("cf", (pos, R)), size=("v3", tuple(size)),
                 Color3uint8=("c3u8", color), Material=("token", MAT[mat]),
                 TopSurface=("token", 0), BottomSurface=("token", 0),
                 Transparency=("float", tr), Reflectance=("float", refl), CanCollide=("bool", collide),
                 CastShadow=("bool", shadow), CanQuery=("bool", query), CanTouch=("bool", collide))
    if shape is not None:
        props["shape"] = ("token", shape)
    inst = new(parent, cls, name, **props)
    PARTS.append(inst)
    return inst


def mbox(parent, name, centre, axes, size, color, mat="SmoothPlastic", **kw):
    R = np.column_stack([D3(*a) for a in axes])
    return part(parent, name, R3(*centre), R, np.array(size, float) * K, color, mat, **kw)


UP = ((1, 0, 0), (0, 0, 1), (0, -1, 0))          # upright, axis-aligned


def aabb(parent, name, x0, y0, z0, x1, y1, z1, color, mat="SmoothPlastic", **kw):
    return mbox(parent, name, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), UP,
                (abs(x1 - x0), abs(z1 - z0), abs(y1 - y0)), color, mat, **kw)


def yaw_axes(phi):
    c, s = math.cos(phi), math.sin(phi)
    return ((c, s, 0), (0, 0, 1), (s, -c, 0))


def ybox(parent, name, cx, cy, z0, w, d, h, phi, color, mat="SmoothPlastic", **kw):
    """Upright box turned by phi; w along its X, d along its Z."""
    return mbox(parent, name, (cx, cy, z0 + h / 2), yaw_axes(phi), (w, h, d), color, mat, **kw)


def wall(parent, name, a, b, z0, h, t, color, mat="SmoothPlastic", out=0.0, **kw):
    """Vertical slab along a->b; its Back face (+Z) looks to the right of a->b."""
    d = b - a
    L, u = np.linalg.norm(d), unit(d)
    n = np.array([u[1], -u[0]])
    c = (a + b) / 2 + n * out
    return mbox(parent, name, (c[0], c[1], z0 + h / 2), ((u[0], u[1], 0), (0, 0, 1), (n[0], n[1], 0)),
                (L, h, t), color, mat, **kw)


def vcyl(parent, name, x, y, z0, h, dia, color, mat="SmoothPlastic", **kw):
    return mbox(parent, name, (x, y, z0 + h / 2), ((0, 0, 1), (1, 0, 0), (0, 1, 0)), (h, dia, dia),
                color, mat, shape=2, **kw)


def ball(parent, name, x, y, z, dia, color, mat="SmoothPlastic", **kw):
    return mbox(parent, name, (x, y, z), UP, (dia, dia, dia), color, mat, shape=0, **kw)


def tri_wedges(a, b, c, thick):
    """A triangle (Roblox points) as two WedgeParts: (centre, rotation, size) each."""
    sq = lambda v: float(np.dot(v, v))
    if sq(b - a) > sq(c - a) and sq(b - a) > sq(c - b):
        a, c = c, a
    elif sq(c - a) > sq(c - b) and sq(c - a) > sq(b - a):
        a, b = b, a
    bc = c - b
    F = b + bc * np.dot(a - b, bc) / np.dot(bc, bc)
    h = np.linalg.norm(a - F)
    out = []
    for B in (b, c):
        d = np.linalg.norm(B - F)
        if h < 1e-3 or d < 1e-3:
            continue
        Y, Z = (a - F) / h, (F - B) / d
        R = np.column_stack([np.cross(Y, Z), Y, Z])
        centre = (a + B) / 2
        # check: the wedge's corners (back-bottom, back-top, front-bottom) land on F, a, B
        for local, want in (((0, -h / 2, d / 2), F), ((0, h / 2, d / 2), a), ((0, -h / 2, -d / 2), B)):
            assert np.allclose(centre + R @ np.array(local), want, atol=1e-6)
        out.append((centre, R, (thick, h, d)))
    return out


def slab(parent, name, outer, holes, z_top, t, color, mat="SmoothPlastic", **kw):
    zc = z_top - t / 2
    for tri in triangulate(outer, holes):
        pts = [R3(p[0], p[1], zc) for p in tri]
        for centre, R, size in tri_wedges(*pts, t * K):
            part(parent, name, centre, R, size, color, mat, cls="WedgePart", **kw)


def values(inst, **vals):
    """Attach StringValue / Color3Value / NumberValue children."""
    for k, v in vals.items():
        if isinstance(v, str):
            new(inst, "StringValue", k, Value=("string", v))
        elif isinstance(v, tuple):
            new(inst, "Color3Value", k, Value=("c3", v))
        else:
            new(inst, "NumberValue", k, Value=("double", float(v)))
    return inst


def sign(inst, text, face="Back", style="fascia", accent=None):
    values(inst, SignText=text, Face=face, Style=style)
    if accent:
        values(inst, Accent=accent)
    return inst


def light(inst, rng=18, brightness=1.0, color=(255, 236, 210), enabled=True, shadows=False, name="Light"):
    new(inst, "PointLight", name, Range=("float", rng), Brightness=("float", brightness), Color=("c3", color),
        Enabled=("bool", enabled), Shadows=("bool", shadows))


# ------------------------------------------------------------------ palette
WHITE, MARBLE, SOFFIT = (243, 243, 240), (228, 224, 216), (236, 236, 233)
GLASS, DOORGLASS, MULL = (160, 200, 212), (176, 212, 222), (176, 184, 190)
CLAD, FRIT, CORE, DARK = (222, 226, 228), (44, 56, 64), (206, 210, 213), (36, 38, 44)
PAVE, WALK, ROAD = (212, 206, 196), (198, 196, 190), (58, 60, 64)
GRASS, TRUNK = (96, 140, 66), (88, 68, 52)


# ------------------------------------------------------------------ lifts
# Every lift is a Model named Elevator that Elevators.server / Elevators.client run:
# Stops (NumberValues 1..n, floor tops in studs, each with a Label and a Title), a Car
# (streamed whole) and Landings (Door<i>, Call<i>, Display<i>). The car is built at the
# first stop; players' screens move it.
CAR_STYLE = {   # walls, wall material, wall transparency, floor, rail, accent strip
    "glass": ((176, 212, 222), "Glass", 0.45, ((90, 96, 102), "Marble"), (200, 204, 208), (120, 230, 255)),
    "steel": ((190, 194, 198), "Metal", 0.0, ((70, 72, 76), "Granite"), (150, 104, 66), (255, 214, 160)),
    "gold": ((206, 178, 120), "Metal", 0.0, ((40, 38, 36), "Marble"), (230, 210, 160), (255, 200, 120)),
    "night": ((30, 34, 44), "Glass", 0.0, ((22, 24, 28), "Marble"), (200, 204, 208), (200, 90, 255)),
}
ELEVATORS = []


def elevator(parent, building, cx, cy, face, stops, cw=2.2, cd=2.0, door=1.2, style="steel", glass_shaft=False,
             vmax=14.0, top=None, pit=1.2, shaft_color=CORE, shaft_lights=False):
    """A lift centred at (cx, cy), doors towards face (an axis unit vector), stopping at stops:
    [(floor top z, label, title)]. Returns the shaft's outer rectangle (x0, y0, x1, y1)."""
    f = np.array(face, float)
    a = np.array([-f[1], f[0]])                 # across the doors, left to right seen from the landing
    C = np.array([cx, cy], float)
    Q = lambda s, r: C + a * s + f * r
    hw, hd = cw / 2, cd / 2
    sw, sb, sf = hw + 0.45, hd + 0.4, hd + 0.45                    # shaft half-width, back and front reach
    door = min(door, hw - 0.08)                 # open doors must still fit inside the shaft
    z_lo, z_hi = stops[0][0] - pit, (top if top is not None else stops[-1][0] + 3.4)
    m = new(parent, "Model", "Elevator")
    values(m, Building=building, MaxSpeed=vmax * K)
    sf_ = new(m, "Folder", "Stops")
    for i, (z, label, title) in enumerate(stops):
        values(new(sf_, "NumberValue", str(i + 1), Value=("double", z * K)), Label=label, Title=title)

    def box(par, name, s0, r0, z0, s1, r1, z1, color, mat="SmoothPlastic", **kw):
        p, q = Q(s0, r0), Q(s1, r1)
        return aabb(par, name, min(p[0], q[0]), min(p[1], q[1]), z0, max(p[0], q[0]), max(p[1], q[1]), z1,
                    color, mat, **kw)

    # shaft: back, sides and a front with an opening at every stop
    sh = new(m, "Folder", "Shaft")
    wall_kw = dict(color=shaft_color, mat="Concrete")
    box(sh, "Shaft wall", -sw, -sb, z_lo, sw, -sb + 0.2, z_hi, **wall_kw)
    for e in (-1, 1):
        box(sh, "Shaft wall", e * (sw - 0.2), -sb + 0.2, z_lo, e * sw, sf - 0.2, z_hi, **wall_kw)
    box(sh, "Shaft cap", -sw, -sb, z_hi, sw, sf, z_hi + 0.25, shaft_color, "Concrete")
    box(sh, "Shaft pit", -sw, -sb, z_lo - 0.2, sw, sf, z_lo, (90, 92, 96), "Concrete")
    front = dict(color=GLASS, mat="Glass", tr=0.5, shadow=False) if glass_shaft else wall_kw
    z = z_lo
    for zs, _, _ in stops:
        if zs - z > 0.05:
            box(sh, "Shaft front", -sw, sf - 0.2, z, sw, sf, zs, **front)
        for e in (-1, 1):
            box(sh, "Shaft front", e * (door / 2 + 0.12), sf - 0.2, zs, e * sw, sf, zs + 2.45, **front)
        z = zs + 2.45
    box(sh, "Shaft front", -sw, sf - 0.2, z, sw, sf, z_hi, **front)
    if glass_shaft:
        for zs in np.arange(z_lo, z_hi, 3.0):
            box(sh, "Shaft frame", -sw, sf - 0.24, zs, sw, sf + 0.04, zs + 0.08, MULL, "Metal")
    for e in (-1, 1):                                                   # guide rails
        box(sh, "Guide rail", e * (sw - 0.32), -0.1, z_lo, e * (sw - 0.2), 0.1, z_hi, (120, 124, 128), "Metal")
    if shaft_lights:                                                    # passing lights tell you the speed
        for zs in np.arange(stops[0][0] + 4.0, z_hi - 1.0, 6.0):
            box(sh, "Shaft light", -hw + 0.2, -sb + 0.18, zs, hw - 0.2, -sb + 0.22, zs + 0.12, (255, 236, 200), "Neon",
                collide=False, shadow=False)

    # landings: doors, frame, call button and floor indicator at every stop
    ld = new(m, "Folder", "Landings")
    rd = hd + 0.17                                                      # landing doors slide behind the shaft front
    for i, (zs, label, title) in enumerate(stops):
        dm = new(ld, "Model", "Door%d" % (i + 1))
        wall(dm, "L", Q(-door / 2 - 0.16, rd), Q(0.01, rd), zs, 2.4, 0.05, (200, 208, 212), "Metal", refl=0.15)
        wall(dm, "R", Q(-0.01, rd), Q(door / 2 + 0.16, rd), zs, 2.4, 0.05, (200, 208, 212), "Metal", refl=0.15)
        values(dm, Slide=(door / 2 + 0.14) * K)
        for e in (-1, 1):
            box(ld, "Door frame", e * (door / 2 + 0.02), sf, zs, e * (door / 2 + 0.2), sf + 0.12, zs + 2.6, MULL, "Metal")
        box(ld, "Door frame", -door / 2 - 0.2, sf, zs + 2.45, door / 2 + 0.2, sf + 0.12, zs + 2.6, MULL, "Metal")
        call = wall(ld, "Call%d" % (i + 1), Q(door / 2 + 0.35, sf + 0.03), Q(door / 2 + 0.6, sf + 0.03), zs + 1.0, 0.4,
                    0.05, (40, 44, 50), "Metal")
        sign(call, "▲▼", style="button")
        new(call, "ProximityPrompt", "ProximityPrompt", ActionText=("string", "Call lift"), ObjectText=("string", title),
            HoldDuration=("float", 0), MaxActivationDistance=("float", 9), RequiresLineOfSight=("bool", False))
        wall(ld, "Display%d" % (i + 1), Q(-0.45, sf + 0.13), Q(0.45, sf + 0.13), zs + 2.62, 0.3, 0.04, (8, 10, 14))

    # the car
    wc, wm, wt, (fc, fm), rail, glow = CAR_STYLE[style]
    z0 = stops[0][0]
    car = new(m, "Model", "Car", ModelStreamingMode=("token", 1))
    floor_ = box(car, "Floor", -hw, -hd, z0 - 0.15, hw, hd, z0, fc, fm)
    car.props["PrimaryPart"] = ("ref", floor_)
    values(car, Slide=(door / 2 + 0.02) * K)
    wkw = dict(tr=wt, shadow=wt == 0, refl=0.1 if wm == "Glass" else 0.05)
    box(car, "Back wall", -hw, -hd, z0, hw, -hd + 0.06, z0 + 2.6, wc, wm, **wkw)
    for e in (-1, 1):
        box(car, "Side wall", e * (hw - 0.06), -hd + 0.06, z0, e * hw, hd, z0 + 2.6, wc, wm, **wkw)
        box(car, "Front return", e * (door / 2 + 0.02), hd - 0.08, z0, e * (hw - 0.06), hd, z0 + 2.6, wc,
            "Metal" if wm == "Glass" else wm)
        box(car, "Handrail", e * (hw - 0.12), -hd + 0.25, z0 + 0.9, e * (hw - 0.07), hd - 0.75, z0 + 0.95, rail, "Metal")
    box(car, "Handrail", -hw + 0.2, -hd + 0.07, z0 + 0.9, hw - 0.2, -hd + 0.12, z0 + 0.95, rail, "Metal")
    box(car, "Header", -door / 2 - 0.02, hd - 0.08, z0 + 2.32, door / 2 + 0.02, hd, z0 + 2.6, wc,
        "Metal" if wm == "Glass" else wm)
    box(car, "Ceiling", -hw, -hd, z0 + 2.6, hw, hd, z0 + 2.72, (232, 232, 230))
    lamp = box(car, "Lamp", -hw + 0.35, -hd + 0.35, z0 + 2.57, hw - 0.35, hd - 0.35, z0 + 2.6, (255, 246, 232), "Neon",
               collide=False, shadow=False)
    light(lamp, rng=10, brightness=0.9)
    box(car, "Glow", -hw + 0.08, -hd + 0.07, z0 + 0.02, hw - 0.08, -hd + 0.09, z0 + 0.1, glow, "Neon", collide=False,
        shadow=False)
    wall(car, "DoorL", Q(-door / 2 - 0.04, hd + 0.04), Q(0.0, hd + 0.04), z0, 2.32, 0.05, (210, 214, 218), "Metal",
         refl=0.15)
    wall(car, "DoorR", Q(0.0, hd + 0.04), Q(door / 2 + 0.04, hd + 0.04), z0, 2.32, 0.05, (210, 214, 218), "Metal",
         refl=0.15)
    wall(car, "CarDisplay", Q(0.35, hd - 0.1), Q(-0.35, hd - 0.1), z0 + 2.36, 0.2, 0.03, (8, 10, 14))
    panel = wall(car, "Panel", Q(hw - 0.08, hd - 0.65), Q(hw - 0.08, hd - 0.25), z0 + 0.85, 0.75, 0.03, (24, 26, 30),
                 "Metal")
    sign(panel, "\n".join(s[1] for s in reversed(stops)), style="directory")
    ELEVATORS.append((building, stops, (min(Q(-sw, -sb)[0], Q(sw, sf)[0]), min(Q(-sw, -sb)[1], Q(sw, sf)[1]),
                                        max(Q(-sw, -sb)[0], Q(sw, sf)[0]), max(Q(-sw, -sb)[1], Q(sw, sf)[1]))))
    r0, r1 = Q(-sw, -sb), Q(sw, sf + 0.25)
    return min(r0[0], r1[0]), min(r0[1], r1[1]), max(r0[0], r1[0]), max(r0[1], r1[1])

# ------------------------------------------------------------------ the place
game_items = []
ws = Inst("Workspace", "Workspace", StreamingEnabled=("bool", True), StreamingMinRadius=("int", 128))
game_items.append(ws)
mall = new(ws, "Model", "Mall")
structure = new(mall, "Folder", "Structure")
doors_f = new(mall, "Folder", "Doors")
esc_f = new(mall, "Folder", "Escalators")
lift_f = new(mall, "Folder", "Lift")
interiors = new(mall, "Folder", "Interiors")
lights_f = new(mall, "Folder", "Lights")
site = new(ws, "Model", "Site")
waypoints = new(ws, "Folder", "Waypoints")
wp_street = new(waypoints, "Folder", "Street")
wp_inside = new(waypoints, "Folder", "Inside")
new(ws, "Folder", "Shoppers")

# columns: the plan's structural grid, kept clear of the atrium, cores and lift
COLS = []
for px in (755, 825, 895, 965, 1015, 1085, 1155, 1225, 1295, 1365):
    for py in (428, 500, 598, 675, 762, 830, 905, 972, 1045, 1115):
        p = P(px, py)
        if inside(p, rect_at(AC, HOLE_HX + 2.5, HOLE_HY + 1.5)):
            continue
        if any(r[0] - 1 < p[0] < r[2] + 1 and r[1] - 1 < p[1] < r[3] + 1 for r in CORES + [SHAFT]):
            continue
        COLS.append(p)


def in_rect(p, r, m=0.0):
    return r[0] - m < p[0] < r[2] + m and r[1] - m < p[1] < r[3] + m


def clear(p, level, r=1.6):
    """A spot that is on the floor, away from columns, cores, the lift and the atrium."""
    poly = POLY[LEVELS[level][3]]
    return (inside(p, offset(poly, 1.2)) and all(np.linalg.norm(p - c) > r for c in COLS)
            and not inside(p, rect_at(AC, HOLE_HX + 1.8, HOLE_HY + 0.8))
            and not any(in_rect(p, c, 1.0) for c in CORES + [SHAFT]))


# ---- floors, ceilings, roof
holes_up = [HOLE, SHAFT_HOLE]
for i, (lid, z, h, key, _) in enumerate(LEVELS):
    poly = POLY[key]
    lv = new(structure, "Folder", lid)
    if i == 0:
        slab(lv, "Floor", poly, [], floor_top(0), 0.25, MARBLE, "Marble")
    else:
        slab(lv, "Floor", poly, holes_up, z, 0.35, MARBLE, "Marble")
    if i < 4:   # ceiling under the next floor, inset so its faces never coincide with that slab
        slab(lv, "Ceiling", offset(poly, 0.03), [offset(HOLE, -0.03), offset(SHAFT_HOLE, -0.03)],
             z + h - 0.012, 0.40, SOFFIT)
roof = new(structure, "Folder", "Roof")
slab(roof, "Roof", POLY["F4"], holes_up, ROOF_Z + 0.5, 0.5, (226, 226, 222), "Concrete")
for a, b in edges(POLY["F4"]):
    wall(roof, "Parapet", a, b, ROOF_Z + 0.5, 1.0, 0.2, (210, 214, 216), "Metal", out=-0.1)
for a, b in edges(HOLE):                              # skylight lantern over the atrium
    wall(roof, "Skylight", a, b, ROOF_Z + 0.5, 2.4, 0.05, GLASS, "Glass", tr=0.55, shadow=False)
    for s in np.linspace(0, 1, 7):
        p = a + (b - a) * s
        wall(roof, "Skylight frame", p - unit(b - a) * 0.05, p + unit(b - a) * 0.05, ROOF_Z + 0.5, 2.45, 0.12, MULL, "Metal")
slab(roof, "Skylight glass", HOLE, [], ROOF_Z + 2.95, 0.05, GLASS, "Glass", tr=0.55, shadow=False)
plant = [px_rect(1060, 380, 1180, 440), px_rect(1260, 600, 1360, 700), px_rect(1100, 720, 1240, 800)]
for r in plant:
    aabb(roof, "Plant", r[0], r[1], ROOF_Z + 0.5, r[2], r[3], ROOF_Z + 2.7, (214, 218, 220), "Metal")
f4 = POLY["F4"]
ys_ = [p[1] for p in f4]
for y in np.arange(min(ys_) + 2.2, max(ys_) - 1.5, 2.6):   # PV rows
    x0 = None
    for x in np.arange(min(p[0] for p in f4) + 1.5, max(p[0] for p in f4) - 1.4, 0.5):
        q = np.array([x, y])
        ok = (inside(q + [0, 1], f4) and inside(q - [0, 1], f4)
              and not inside(q, rect_at(AC, HOLE_HX + 2.5, HOLE_HY + 2.5))
              and not any(in_rect(q, r, 1.2) for r in CORES + [SHAFT] + plant))
        if ok and x0 is None:
            x0 = x
        if (not ok or x >= max(p[0] for p in f4) - 1.9) and x0 is not None:
            if x - x0 > 3:
                mbox(roof, "Solar panel", ((x0 + x) / 2, y, ROOF_Z + 1.0),
                     ((1, 0, 0), (0, math.sin(12 * DEG), math.cos(12 * DEG)), (0, -math.cos(12 * DEG), math.sin(12 * DEG))),
                     (x - x0, 0.06, 1.7), (24, 38, 70), "Glass", refl=0.15)
            x0 = None

# ---- columns and cores
for i, (lid, z, h, key, _) in enumerate(LEVELS):
    lv = structure.kids[i]
    above = [POLY[LEVELS[j][3]] for j in range(i, 5)]
    for c in COLS:
        if not any(inside(c, p) for p in above):
            continue
        if i == 4 and (in_rect(c, HALL_A, 0.5) or in_rect(c, HALL_B, 0.5)):
            continue
        vcyl(lv, "Column", c[0], c[1], floor_top(i), wall_top(i) - floor_top(i) + 0.4, 0.6, WHITE)
    for r in CORES:
        aabb(lv, "Core", r[0], r[1], floor_top(i), r[2], r[3], wall_top(i) + 0.3, CORE, "Concrete")

# ---- facades
DOORS = [(0, P(1090, 733), 3.2), (0, P(880, 733), 3.2), (0, P(657, 560), 3.2), (4, P(1010, 905), 2.4)]


def panel(parent, a, b, z0, z1, kind):
    if kind == "glass":
        return wall(parent, "Glass", a, b, z0, z1 - z0, 0.05, GLASS, "Glass", tr=0.55, refl=0.04, shadow=False)
    if kind == "frit":
        return wall(parent, "Fritted glass", a, b, z0, z1 - z0, 0.08, FRIT, "Glass", tr=0.18, refl=0.08)
    if kind == "clad":
        return wall(parent, "Cladding", a, b, z0, z1 - z0, 0.25, CLAD, "Metal")
    if kind == "led":
        w = wall(parent, "LED wall", a, b, z0, z1 - z0, 0.15, (18, 26, 60), "Neon")
        return sign(w, "GLASS MALL", style="led", accent=(220, 60, 190))


def auto_door(parent, a, b, z0, name="AutoDoor", h=2.75, out=0.09):
    m = new(parent, "Model", name)
    u, half = unit(b - a), np.linalg.norm(b - a) / 2
    left = wall(m, "L", a, a + u * (half + 0.04), z0, h, 0.06, DOORGLASS, "Glass", tr=0.4, out=out, shadow=False)
    right = wall(m, "R", a + u * (half - 0.04), b, z0, h, 0.06, DOORGLASS, "Glass", tr=0.4, out=out, shadow=False)
    for p in (left, right):
        new(p, "PathfindingModifier", "Door", PassThrough=("bool", True), Label=("string", "Door"))
    values(m, Slide=half * K)
    return m


def facade(parent, i, segs):
    z0, z1 = floor_top(i), wall_top(i)
    for a, b, kind in segs:
        L, u = np.linalg.norm(b - a), unit(b - a)
        cuts = []
        for lvl, c, w in DOORS:
            t = float(np.dot(c - a, u))
            if lvl == i and abs(cross2(a, b, c)) / L < 0.3 and 0 < t < L:
                cuts.append((t - w / 2, t + w / 2))
        cuts.sort()
        s = 0.0
        for d0, d1 in cuts + [(L, L)]:
            if d0 - s > 0.05:
                panel(parent, a + u * s, a + u * d0, z0, z1, kind)
            s = d1
        for d0, d1 in cuts:
            pa, pb = a + u * d0, a + u * d1
            panel(parent, pa, pb, z0 + 2.9, z1, kind)
            wall(parent, "Door head", pa, pb, z0 + 2.75, 0.15, 0.22, MULL, "Metal")
            for q in (pa, pb):
                wall(parent, "Door jamb", q - u * 0.05, q + u * 0.05, z0, 2.9, 0.22, MULL, "Metal")
            auto_door(doors_f, pa, pb, z0)
        if kind in ("glass", "frit"):
            n = max(1, round(L / 1.8))
            for k in range(n + 1):
                s = L * k / n
                if any(d0 - 0.2 < s < d1 + 0.2 for d0, d1 in cuts):
                    continue
                q = a + u * s
                wall(parent, "Mullion", q - u * 0.04, q + u * 0.04, z0, z1 - z0, 0.2, MULL, "Metal")


def outward(a, b, poly):
    """Order a segment so its right-hand side faces out of the polygon."""
    n = np.array([unit(b - a)[1], -unit(b - a)[0]])
    return (a, b) if not inside((a + b) / 2 + n * 0.3, poly) else (b, a)


for i, (lid, z, h, key, _) in enumerate(LEVELS):
    poly, lv = POLY[key], structure.kids[i]
    if i < 4:
        segs = []
        for a, b in edges(poly):
            north = a[1] > NORTH - 0.01 and b[1] > NORTH - 0.01
            east = a[0] > EAST - 0.01 and b[0] > EAST - 0.01
            segs.append((a, b, "clad" if north or (i == 0 and east) else "glass"))
    else:
        spec = [((635, 337), (1010, 337), "frit"), ((635, 830), (635, 337), "frit"), ((1010, 830), (635, 830), "led"),
                ((1010, 337), (1395, 337), "glass"), ((1395, 337), (1395, 678), "glass"),
                ((1395, 678), (1395, 1157), "frit"), ((1395, 1157), (1010, 980), "frit"), ((1010, 980), (1010, 830), "frit")]
        segs = [outward(P(*a), P(*b), poly) + (k,) for a, b, k in spec]
    facade(lv, i, segs)

# ---- atrium balustrades and escalators
STRIP = lambda p: -1 if p % 2 == 0 else 1           # which long side of the atrium a flight uses
E_OFF = A_SIDE / 2 + 0.95
for i in range(1, 5):
    lv = structure.kids[i]
    gaps = {-1: [], 1: []}
    gaps[-1].append(sorted([STRIP(i - 1) * (E_OFF - 0.85), STRIP(i - 1) * (E_OFF + 0.85)]))   # arrival
    if i < 4:
        gaps[1].append(sorted([STRIP(i) * (E_OFF - 0.85), STRIP(i) * (E_OFF + 0.85)]))        # departure
    runs = []
    for e in (-1, 1):
        s = -HOLE_HY
        for g0, g1 in sorted(gaps[e]) + [(HOLE_HY, HOLE_HY)]:
            if g0 - s > 0.05:
                runs.append((hole_pt(e * HOLE_HX, s), hole_pt(e * HOLE_HX, g0)))
            s = g1
    for e in (-1, 1):
        runs.append((hole_pt(-HOLE_HX, e * HOLE_HY), hole_pt(HOLE_HX, e * HOLE_HY)))
    for a, b in runs:
        wall(lv, "Atrium balustrade", a, b, floor_top(i), 1.1, 0.04, GLASS, "Glass", tr=0.6, shadow=False)
        wall(lv, "Handrail", a, b, floor_top(i) + 1.1, 0.06, 0.08, MULL, "Metal")

for p in range(4):
    k, e = STRIP(p), 1
    zb, zt = floor_top(p), floor_top(p + 1)
    c = AC + EY * (k * E_OFF)
    b2, t2 = c + EX * e * (HOLE_HX + 0.15), c - EX * e * (HOLE_HX + 0.15)
    B3, T3 = np.array([b2[0], b2[1], zb]), np.array([t2[0], t2[1], zt])
    X = unit(T3 - B3)
    Zd = np.array([EY[0], EY[1], 0.0])
    Y = np.cross(Zd, X)
    if Y[2] < 0:
        Zd, Y = -Zd, np.cross(-Zd, X)
    L, mid = np.linalg.norm(T3 - B3), (B3 + T3) / 2
    axes = (tuple(X), tuple(Y), tuple(Zd))
    m = new(esc_f, "Model", "Escalator %s-%s" % (LEVELS[p][0], LEVELS[p + 1][0]))
    mbox(m, "Tread", mid - Y * 0.15, axes, (L, 0.3, 1.6), (112, 118, 124), "DiamondPlate")
    mbox(m, "Truss", mid - Y * 0.65, axes, (L, 0.7, 1.75), (186, 192, 196), "Metal")
    for sgn in (-1, 1):
        mbox(m, "Side glass", mid + Y * 0.55 + Zd * sgn * 0.84, axes, (L, 1.0, 0.04), GLASS, "Glass", tr=0.5, shadow=False)
        mbox(m, "Handrail", mid + Y * 1.07 + Zd * sgn * 0.84, axes, (L, 0.08, 0.12), (24, 24, 26))
    phi = math.atan2(EX[1], EX[0])
    for q, zq in ((c + EX * e * (HOLE_HX + 0.75), zb), (c - EX * e * (HOLE_HX + 0.75), zt)):
        ybox(m, "Landing plate", q[0], q[1], zq, 1.2, 1.6, 0.02, phi, (150, 156, 160), "DiamondPlate")

# ---- lift: a panoramic glass car behind a glass shaft front, one stop per floor
x0, y0, x1, y1 = SHAFT
xc = (x0 + x1) / 2
elevator(lift_f, "Glass Mall", xc, (y0 + y1) / 2 + 0.03, (0, -1),
         [(floor_top(i), LEVELS[i][0], LEVELS[i][4]) for i in range(5)],
         cw=x1 - x0 - 0.9, cd=y1 - y0 - 0.91, door=1.8, style="glass", glass_shaft=True, top=ROOF_Z + 2.0, vmax=12.0)
for i in range(5):
    zf = floor_top(i)
    directory = aabb(lift_f, "Directory", xc - 2.5, y0 - 0.06, zf + 0.9, xc - 1.3, y0, zf + 2.3, (20, 24, 28))
    sign(directory, "%s  ·  YOU ARE HERE\n\n4F  Cinemas · Terrace\n3F  Arcade · Games\n2F  Food court\n1F  Fashion\nGF  Shops · Exit"
         % LEVELS[i][0], style="directory")

# ---- shops
SHOPS = {
    0: [("LOOM", (232, 90, 70)), ("PAGEBOUND", (90, 150, 230)), ("VOLT", (250, 200, 40)), ("PETAL & STEM", (235, 120, 170))],
    1: [("SOLE STORY", (240, 140, 60)), ("NOOK HOME", (110, 190, 150)), ("ARC TOYS", (250, 90, 90)), ("HUE BEAUTY", (210, 120, 220))],
    2: [("KAAPI CORNER", (200, 130, 70)), ("DOSA HOUSE", (240, 180, 40)), ("NOODLE BAR", (230, 70, 60)), ("GELATO LAB", (120, 210, 220))],
    3: [("PIXEL PLAY", (120, 90, 240)), ("GAME ON", (60, 220, 140)), ("SPORTS DEPOT", (60, 140, 240)), ("BRICKWORKS", (240, 100, 60))],
}
WEST_1F = [("TRAILHEAD", (90, 170, 90)), ("STITCH & CO", (230, 170, 90)), ("SPROUT KIDS", (100, 200, 230))]


def shop_row(parent, level, units, a, b, depth):
    """Units side by side along a->b (their fronts); the row's back is depth behind, to the left."""
    z, top = floor_top(level), wall_top(level)
    hg = 3.2 if level == 0 else 2.1
    u = unit(b - a)
    n = np.array([u[1], -u[0]])
    L = np.linalg.norm(b - a) / len(units)
    for k, (name, accent) in enumerate(units):
        fa, fb = a + u * (k * L), a + u * ((k + 1) * L)
        sh = new(parent, "Model", name.title())
        for q in ([fa] if k == 0 else []) + [fb]:
            wall(sh, "Partition", q, q - n * depth, z, top - z + 0.3, 0.15, WHITE)
        m = (fa + fb) / 2
        wall(sh, "Shopfront", fa + u * 0.1, m - u * 1.1, z, hg, 0.05, GLASS, "Glass", tr=0.5, shadow=False)
        wall(sh, "Shopfront", m + u * 1.1, fb - u * 0.1, z, hg, 0.05, GLASS, "Glass", tr=0.5, shadow=False)
        fascia = wall(sh, "Fascia", fa, fb, z + hg, 0.55, 0.22, (28, 30, 34), out=0.05)
        sign(fascia, name)
        wall(sh, "Neon strip", fa, fb, z + hg - 0.05, 0.05, 0.24, accent, "Neon", out=0.05, collide=False)
        if level == 0:
            wall(sh, "Bulkhead", fa, fb, z + hg + 0.55, top - z - hg - 0.25, 0.2, WHITE)
        back = m - n * depth
        wall(sh, "Shelf", back - u * (L / 2 - 0.5), back + u * (L / 2 - 0.5), z, 2.0, 0.45, (245, 244, 240), out=0.3)
        wall(sh, "Shelf stock", back - u * (L / 2 - 0.7), back + u * (L / 2 - 0.7), z + 0.5, 1.2, 0.3, accent, out=0.32)
        phi = math.atan2(u[1], u[0])
        for s in (-1, 1):
            q = m - n * (depth * 0.5) + u * s * 1.4
            ybox(sh, "Display", q[0], q[1], z, 1.4, 0.8, 0.85, phi, tuple(int(c * 0.35 + 160) for c in accent))
        light(sh.kids[-1], rng=16, brightness=0.8)
        wp = m + n * 1.5
        aabb(wp_inside, "Shop", wp[0] - 0.2, wp[1] - 0.2, z + 0.4, wp[0] + 0.2, wp[1] + 0.2, z + 0.8, (255, 0, 0),
             tr=1, collide=False, query=False, shadow=False)


shops_f = new(interiors, "Folder", "Shops")
for level, units in SHOPS.items():
    shop_row(shops_f, level, units, np.array([0.4, 63.6]), np.array([27.9, 63.6]), 70.02 - 63.6)
shop_row(shops_f, 1, WEST_1F, np.array([4.8, 40.0]), np.array([4.8, 61.0]), 4.8 + 1.45)


def inside_wp(x, y, level, name="Spot"):
    z = floor_top(level)
    aabb(wp_inside, name, x - 0.2, y - 0.2, z + 0.4, x + 0.2, y + 0.2, z + 0.8, (255, 0, 0), tr=1, collide=False,
         query=False, shadow=False)


def seat(parent, x, y, z, phi, color=(150, 30, 40), back=True, w=0.5):
    """A Seat facing along its -Z (towards what phi points it at)."""
    st = ybox(parent, "Seat", x, y, z + 0.38, w, 0.5, 0.1, phi, color, "Fabric", cls="Seat")
    st.props["Disabled"] = ("bool", False)
    if back:
        c, s = math.cos(phi), math.sin(phi)
        bz = np.array([x, y]) + np.array([s, -c]) * 0.27
        ybox(parent, "Seat back", bz[0], bz[1], z + 0.38, w, 0.08, 0.55, phi, color, "Fabric")
    return st


# ---- GF: atrium tree, kiosks, benches, info desk
gf = new(interiors, "Folder", "GF")
aabb(gf, "Atrium planter", AC[0] - 1.6, AC[1] - 1.6, 0.03, AC[0] + 1.6, AC[1] + 1.6, 0.6, (226, 222, 214), "Marble")
aabb(gf, "Atrium planter soil", AC[0] - 1.45, AC[1] - 1.45, 0.6, AC[0] + 1.45, AC[1] + 1.45, 0.65, GRASS, "Grass")
vcyl(gf, "Atrium tree", AC[0], AC[1], 0.6, 7.5, 0.5, TRUNK, "Wood")
for k in range(9):
    ang, rr = k * 2.4, 0.6 + 1.6 * rnd.random()
    ball(gf, "Atrium tree canopy", AC[0] + rr * math.cos(ang), AC[1] + rr * math.sin(ang), 6.4 + 3.2 * rnd.random(),
         2.6 + 1.6 * rnd.random(), rnd.choice([(62, 106, 51), (74, 122, 59), (54, 89, 43), (85, 132, 63)]), "Grass",
         collide=False)
for k in range(8):
    ang = k * math.pi / 4 + math.pi / 8
    q = AC + np.array([math.cos(ang), math.sin(ang)]) * 2.6
    seat(gf, q[0], q[1], 0.03, ang + math.pi / 2 + math.pi, color=(160, 120, 80), back=False, w=0.9)
kiosk_spots = [np.array(p) for p in ((10.5, 50.5), (20.0, 52.5), (16.0, 44.0), (27.5, 46.0), (52.0, 44.0), (57.0, 52.0))]
for q, (name, accent) in zip([q for q in kiosk_spots if clear(q, 0, 2.2)][:4],
                            [("SIP & GO", (90, 200, 220)), ("CASE CO", (240, 120, 60)), ("SCENTS", (220, 120, 200)),
                             ("SWEET SPOT", (240, 200, 60))]):
    k_ = new(gf, "Model", "Kiosk " + name.title())
    aabb(k_, "Counter", q[0] - 1.2, q[1] - 0.7, 0.03, q[0] + 1.2, q[1] + 0.7, 1.1, (242, 240, 236))
    aabb(k_, "Counter top", q[0] - 1.3, q[1] - 0.8, 1.1, q[0] + 1.3, q[1] + 0.8, 1.16, accent)
    for sx in (-1.15, 1.15):
        vcyl(k_, "Post", q[0] + sx, q[1], 1.16, 1.4, 0.08, MULL, "Metal")
    canopy = aabb(k_, "Canopy", q[0] - 1.4, q[1] - 0.9, 2.56, q[0] + 1.4, q[1] + 0.9, 2.86, (30, 32, 36))
    sign(canopy, name)
    aabb(k_, "Canopy glow", q[0] - 1.4, q[1] - 0.9, 2.53, q[0] + 1.4, q[1] + 0.9, 2.56, accent, "Neon", collide=False)
    inside_wp(q[0], q[1] - 1.8, 0, "Kiosk")
desk = aabb(gf, "Information desk", 30.0, 43.3, 0.03, 33.6, 44.3, 1.1, (240, 238, 234), "Marble")
sign(aabb(gf, "Information sign", 30.0, 43.2, 1.1, 33.6, 43.3, 1.6, (20, 24, 28)), "INFORMATION")
for x in (15.0, 25.0, 45.0, 55.0):
    inside_wp(x, 40.0, 0, "Atrium")
inside_wp(AC[0] - 3.0, AC[1] - 2.5, 0, "Atrium")

# ---- 1F: fashion floor displays
f1 = new(interiors, "Folder", "1F")
palette = [(230, 90, 70), (60, 120, 200), (40, 44, 52), (240, 190, 60), (90, 170, 120), (200, 120, 200)]
for zone in ((50.0, 25.0, 61.5, 46.0), (9.0, 30.0, 28.0, 44.0)):
    for x in np.arange(zone[0], zone[2], 3.6):
        for y in np.arange(zone[1], zone[3], 3.0):
            q = np.array([x, y])
            if not clear(q, 1, 1.4):
                continue
            ybox(f1, "Rail", x, y, floor_top(1), 2.2, 0.5, 1.35, 0, (200, 204, 208), "Metal")
            ybox(f1, "Clothes", x, y, floor_top(1) + 0.45, 2.0, 0.45, 0.85, 0, rnd.choice(palette), "Fabric",
                 collide=False)
for q in ((55.0, 30.0), (56.0, 42.0), (15.0, 37.0), (24.0, 38.0)):
    inside_wp(q[0], q[1] + 1.4, 1, "Fashion")

# ---- 2F: food court
f2 = new(interiors, "Folder", "2F")
z2 = floor_top(2)
for zone in ((13.5, 37.4, 23.8, 54.6), (27.7, 34.7, 44.8, 45.0)):
    for x in np.arange(zone[0] + 1.2, zone[2] - 0.8, 3.3):
        for y in np.arange(zone[1] + 1.2, zone[3] - 0.8, 3.3):
            q = np.array([x, y])
            if not clear(q, 2, 1.9):
                continue
            t_ = new(f2, "Model", "Table")
            vcyl(t_, "Table top", x, y, z2 + 0.72, 0.05, 1.1, (245, 243, 238), "Marble")
            vcyl(t_, "Table leg", x, y, z2, 0.72, 0.12, (40, 40, 44), "Metal")
            for k in range(4):
                ang = k * math.pi / 2 + math.pi / 4
                p = q + np.array([math.cos(ang), math.sin(ang)]) * 0.95
                seat(t_, p[0], p[1], z2, ang + math.pi / 2, color=rnd.choice([(230, 120, 60), (60, 150, 170), (240, 190, 70)]))
for q in ((18.5, 45.0), (36.0, 40.0), (30.0, 37.0)):
    inside_wp(q[0], q[1], 2, "Food court")
sign(aabb(f2, "Food court sign", 13.5, 55.6, z2 + 2.0, 23.8, 55.75, z2 + 2.55, (28, 30, 34)), "FOOD COURT")

# ---- 3F: arcade
f3 = new(interiors, "Folder", "3F")
z3 = floor_top(3)
for y in np.arange(34.0, 55.0, 3.2):
    for x in np.arange(2.5, 21.5, 1.3):
        q = np.array([x, y])
        if not clear(q, 3, 1.1):
            continue
        face_n = 1 if int((y - 34.0) / 3.2) % 2 == 0 else -1     # rows face alternately north and south
        phi = 0.0 if face_n < 0 else math.pi
        cab = new(f3, "Model", "Arcade machine")
        ybox(cab, "Cabinet", x, y, z3, 0.9, 0.8, 1.8, phi, (26, 26, 36))
        glow = rnd.choice([(255, 60, 160), (60, 220, 255), (255, 210, 60), (120, 255, 120), (170, 90, 255)])
        sp = q + np.array([0, face_n * 0.41])
        ybox(cab, "Screen", sp[0], sp[1], z3 + 1.0, 0.7, 0.03, 0.5, phi, glow, "Neon", collide=False)
        ybox(cab, "Marquee", sp[0], sp[1], z3 + 1.62, 0.8, 0.04, 0.14, phi, glow, "Neon", collide=False)
sign(aabb(f3, "Arcade sign", 2.0, 56.6, z3 + 2.0, 21.0, 56.75, z3 + 2.55, (28, 30, 34)), "ARCADE")
for q in ((11.0, 32.0), (22.5, 46.0), (12.0, 57.5)):
    inside_wp(q[0], q[1], 3, "Arcade")

# ---- 4F: two cinemas, lobby counter
f4f = new(interiors, "Folder", "4F")
z4 = floor_top(4)


def cinema(name, rect, screen_side, door_side, door_at, title):
    """Hall with a screen, stepped rows of seats rising away from it, and a door at floor level by the screen."""
    x0_, y0_, x1_, y1_ = rect
    hall = new(f4f, "Model", name)
    h_ = wall_top(4) - z4
    corners = [np.array(c, float) for c in ((x0_, y0_), (x1_, y0_), (x1_, y1_), (x0_, y1_))]
    door_wp = None
    for side, (a, b) in zip("SENW", edges(corners)):     # CCW, so each wall's right-hand side is outside
        if side != door_side:
            wall(hall, "Hall wall", a, b, z4, h_, 0.2, DARK)
            continue
        u = unit(b - a)
        n = np.array([u[1], -u[0]])
        d0 = float(np.dot(door_at - a, u))
        wall(hall, "Hall wall", a, a + u * (d0 - 1.3), z4, h_, 0.2, DARK)
        wall(hall, "Hall wall", a + u * (d0 + 1.3), b, z4, h_, 0.2, DARK)
        wall(hall, "Hall wall", a + u * (d0 - 1.3), a + u * (d0 + 1.3), z4 + 2.9, h_ - 2.9, 0.2, DARK)
        sign(wall(hall, "Hall sign", a + u * (d0 - 1.6), a + u * (d0 + 1.6), z4 + 3.0, 0.6, 0.25, (28, 30, 34), out=0.05),
             name.upper())
        door_wp = door_at + n * 1.5
    aabb(hall, "Hall ceiling", x0_, y0_, z4 + h_ - 0.4, x1_, y1_, z4 + h_ - 0.3, (24, 26, 30))
    fwd = np.array([1.0, 0.0]) if screen_side == "W" else np.array([0.0, 1.0])   # from the screen to the back
    acr = np.array([fwd[1], -fwd[0]])
    width = (y1_ - y0_) if screen_side == "W" else (x1_ - x0_)
    s0 = np.array([x0_ + 0.5, (y0_ + y1_) / 2]) if screen_side == "W" else np.array([(x0_ + x1_) / 2, y0_ + 0.5])
    phi = math.atan2(fwd[0], -fwd[1])        # +Z along fwd: seats look back at the screen, which shows on its Back face
    scr = ybox(hall, "Screen", s0[0], s0[1], z4 + 1.4, width * 0.8, 0.1, 3.4, phi, (235, 238, 242), "Neon")
    sign(scr, "NOW SHOWING\n" + title, face="Back", style="screen", accent=(230, 80, 60))
    rows, depth, rise = 8, 1.2, 0.3
    for r in range(rows):
        centre = s0 + fwd * (7.0 + r * depth + depth / 2)
        if r > 0:
            ybox(hall, "Tier", centre[0], centre[1], z4, width - 0.4, depth, r * rise, phi, (60, 22, 30), "Fabric")
        n_seats = int((width - 3.4) / 0.9)
        for k in range(n_seats):
            p_ = centre + acr * ((k - (n_seats - 1) / 2) * 0.9 + 0.6)
            seat(hall, p_[0], p_[1], z4 + r * rise, phi)
    back_from = s0 + fwd * (7.0 + rows * depth)
    far = x1_ if screen_side == "W" else y1_
    left = far - float(np.dot(back_from, fwd)) - 0.2
    if left > 0.5:
        bc = back_from + fwd * left / 2
        ybox(hall, "Projection deck", bc[0], bc[1], z4, width - 0.4, left, rows * rise, phi, (40, 20, 26))
    inside_wp(door_wp[0], door_wp[1], 4, "Cinema")


cinema("Cinema 1", HALL_A, "W", "S", np.array([HALL_A[0] + 4.0, HALL_A[1]]), "MONSOON SKIES")
cinema("Cinema 2", HALL_B, "S", "W", np.array([HALL_B[0], HALL_B[1] + 3.5]), "THE LAST METRO HOME")
counter = aabb(f4f, "Ticket counter", 36.0, 33.0, z4, 42.0, 34.0, z4 + 1.1, (30, 32, 36))
sign(aabb(f4f, "Ticket sign", 36.0, 32.85, z4 + 2.4, 42.0, 33.0, z4 + 3.0, (30, 32, 36)), "TICKETS · POPCORN", face="Back")
aabb(f4f, "Counter glow", 36.0, 32.9, z4 + 1.1, 42.0, 34.0, z4 + 1.15, (255, 170, 60), "Neon", collide=False)
inside_wp(39.0, 30.0, 4, "Cinema lobby")

# ---- terrace on top of 3F where 4F steps back
terrace = new(interiors, "Folder", "Terrace")
tri = [P(698, 830), P(1010, 830), np.array([P(1010, 0)[0], P(660, 812)[1] + (P(1395, 1157)[1] - P(660, 812)[1])
                                           * (P(1010, 0)[0] - P(660, 812)[0]) / (P(1395, 1157)[0] - P(660, 812)[0])])]
slab(terrace, "Terrace lawn", tri, [], z4 + 0.04, 0.06, GRASS, "Grass")
a, b = outward(tri[0], tri[2], ccw(tri))
wall(terrace, "Terrace balustrade", a, b, z4, 1.1, 0.04, GLASS, "Glass", tr=0.6, shadow=False)
wall(terrace, "Handrail", a, b, z4 + 1.1, 0.06, 0.08, MULL, "Metal")
for q in (P(760, 850), P(850, 868), P(940, 892)):
    vcyl(terrace, "Trunk", q[0], q[1], z4, 2.4, 0.2, TRUNK, "Wood")
    for k in range(5):
        ball(terrace, "Blossom", q[0] + rnd.uniform(-0.8, 0.8), q[1] + rnd.uniform(-0.8, 0.8), z4 + 2.6 + rnd.uniform(0, 1),
             1.4 + rnd.uniform(0, 0.6), rnd.choice([(228, 141, 179), (240, 166, 197), (107, 138, 66)]), "Grass", collide=False)
for q, ang in ((P(800, 845), 0.45), (P(900, 875), 0.45)):
    seat(terrace, q[0], q[1] + 1.2, z4, ang + math.pi, color=(160, 120, 80), back=False, w=1.0)
inside_wp(*(P(900, 862) + np.array([0, 0.6])), 4, "Terrace")

# ---- ceiling lights (not in the cinemas)
for i, (lid, z, h, key, _) in enumerate(LEVELS):
    poly = offset(POLY[key], 1.5)
    zc = ceiling(i)
    n_ = 0
    for x in np.arange(-1.0, 64.0, 6.5):
        for y in np.arange(1.0, 70.0, 6.5):
            q = np.array([x, y])
            if not inside(q, poly) or inside(q, rect_at(AC, HOLE_HX + 1, HOLE_HY + 1)):
                continue
            if any(in_rect(q, r, 0.8) for r in CORES + [SHAFT]) or (i == 4 and (in_rect(q, HALL_A, 0.3) or in_rect(q, HALL_B, 0.3))):
                continue
            p_ = aabb(lights_f, "Ceiling light", x - 0.6, y - 0.6, zc - 0.04, x + 0.6, y + 0.6, zc, (255, 248, 236), "Neon",
                      collide=False, shadow=False)
            n_ += 1
            if n_ % 3 == 0:
                light(p_, rng=20, brightness=0.9)

# ------------------------------------------------------------------ Glass City
# The mall sits in a city now: a ring highway round a grid of avenues and streets, the
# diagonal boulevard past the mall running corner to corner, and a district in each block -
# suburbs, midtown, downtown towers, Central Park, the VAYU hotel, uptown and a stunt park,
# with a beach on the bay outside the ring. Model metres throughout, as above.
city = new(ws, "Folder", "City")
roads_f = new(city, "Folder", "Roads")
walks_f = new(city, "Folder", "Sidewalks")
city_lamps = new(city, "Folder", "StreetLights")
coins_f = new(ws, "Folder", "Coins")
spawns_f = new(ws, "Folder", "CarSpawns")
portals_f = new(ws, "Folder", "Portals")
traffic_f = new(site, "Folder", "Traffic")
MARK, YELLOW, MEDIAN = (236, 232, 220), (240, 196, 40), (206, 206, 200)
CONC = [(222, 216, 206), (210, 206, 198), (230, 226, 218), (200, 204, 206), (226, 214, 196), (190, 184, 176)]
BRIGHT = [(232, 132, 100), (236, 200, 128), (128, 180, 204), (156, 198, 146), (226, 166, 188), (240, 236, 228),
          (204, 146, 106), (120, 150, 196)]
GLASSES = [(52, 84, 100), (60, 70, 90), (84, 98, 88), (30, 50, 72), (104, 116, 126), (70, 96, 120)]
FRAMES = [(226, 228, 230), (44, 48, 54), (186, 176, 156), (150, 156, 162)]

ground = new(site, "Folder", "Ground")
court = [P(950, 733), P(1230, 733), P(1185, 1048), P(830, 876)]
slab(ground, "Entrance court", court, [], 0.0, 0.1, PAVE, "Slate")
slab(ground, "Forecourt", [P(657, 733), P(1395, 733), P(1395, 760), P(657, 760)], [], 0.0, 0.1, PAVE, "Slate")
aabb(ground, "West path", -4.7, 49.6, -0.1, 0.0, 52.8, 0.0, PAVE, "Slate")
diagA, diagB = P(575, 772), P(1474, 1195)
dDir = unit(diagB - diagA)
dOut = np.array([dDir[1], -dDir[0]])             # across the road, away from the mall
phi_road = math.atan2(dDir[1], dDir[0])

CITY_GROUND = (-480.0, -540.0, 348.0, 600.0)
LAKE = (96.0, 22.0, 140.0, 64.0)


def tiles(x0, y0, x1, y1, step=380.0):
    """Split a rectangle into pieces no longer than step (a part stops at 2048 studs)."""
    nx, ny = max(1, math.ceil((x1 - x0) / step - 1e-9)), max(1, math.ceil((y1 - y0) / step - 1e-9))
    for i in range(nx):
        for j in range(ny):
            yield (x0 + (x1 - x0) * i / nx, y0 + (y1 - y0) * j / ny,
                   x0 + (x1 - x0) * (i + 1) / nx, y0 + (y1 - y0) * (j + 1) / ny)


gx0, gy0, gx1, gy1 = CITY_GROUND
lx0, ly0, lx1, ly1 = LAKE
for r in ((gx0, gy0, lx0, gy1), (lx1, gy0, gx1, gy1), (lx0, gy0, lx1, ly0), (lx0, ly1, lx1, gy1)):
    for x0, y0, x1, y1 in tiles(*r):
        aabb(ground, "Grass", x0, y0, -6.0, x1, y1, -0.08, GRASS, "Grass")
aabb(ground, "Lake bed", lx0, ly0, -4.4, lx1, ly1, -4.0, (92, 84, 66), "Slate")


def R4(x0, y0, x1, y1):
    return [np.array(p, float) for p in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]


def clip(poly, f):
    """The part of a convex polygon where the linear function f is >= 0."""
    out = []
    for i in range(len(poly)):
        a, b = poly[i - 1], poly[i]
        fa, fb = f(a), f(b)
        if (fa >= 0) != (fb >= 0):
            out.append(a + (b - a) * (fa / (fa - fb)))
        if fb >= 0:
            out.append(b)
    pts = []
    for p in out:
        if not pts or np.linalg.norm(p - pts[-1]) > 1e-6:
            pts.append(p)
    if len(pts) > 1 and np.linalg.norm(pts[0] - pts[-1]) < 1e-6:
        pts.pop()
    return pts


def clip_rect(poly, x0, y0, x1, y1):
    for f in (lambda p: p[0] - x0, lambda p: x1 - p[0], lambda p: p[1] - y0, lambda p: y1 - p[1]):
        poly = clip(poly, f)
        if len(poly) < 3:
            return []
    return poly


def cslab(parent, name, poly, z_top, t, color, mat="SmoothPlastic", **kw):
    """A slab under a convex outline, as a fan of wedge pairs."""
    zc = z_top - t / 2
    for i in range(1, len(poly) - 1):
        pts = [R3(p[0], p[1], zc) for p in (poly[0], poly[i], poly[i + 1])]
        for centre, R, size in tri_wedges(*pts, t * K):
            part(parent, name, centre, R, size, color, mat, cls="WedgePart", **kw)


def ramp(parent, name, cx, cy, z0, run, width, height, yaw, color, mat="SmoothPlastic", **kw):
    """A wedge that rises by height over run towards (cos yaw, sin yaw)."""
    c, s = math.cos(yaw), math.sin(yaw)
    return mbox(parent, name, (cx, cy, z0 + height / 2), ((-s, c, 0), (0, 0, 1), (c, s, 0)),
                (width, height, run), color, mat, cls="WedgePart", **kw)


def tree(parent, q, h, rr, palette, n=5, z0=-0.1):
    tr = new(parent, "Model", "Tree")
    vcyl(tr, "Trunk", q[0], q[1], z0, h * 0.62, 0.35, TRUNK, "Wood")
    for k in range(n):
        u_, ang = rnd.random(), k * 2.4 + rnd.random()
        d = rr * 0.65 * math.sqrt(u_)
        ball(tr, "Canopy", q[0] + d * math.cos(ang), q[1] + d * math.sin(ang), z0 + h * (0.62 + 0.28 * (1 - u_)),
             rr * (0.9 + 0.45 * rnd.random()), rnd.choice(palette), "Grass", collide=False)
    return tr


# ---- the boulevard past the mall, and the ring and grid it runs across
dk = lambda p: float(np.dot(np.asarray(p, float) - diagA, dOut))     # across the boulevard
dt = lambda p: float(np.dot(np.asarray(p, float) - diagA, dDir))     # along it
DLO, DHI = 0.0, 28.0                      # the boulevard and both its pavements, across from diagA
RW, RE, RS, RN, RH = -185.0, 330.0, -245.0, 305.0, 9.0      # ring highway centre lines, half-width
AH, SW = 6.0, 3.0                                            # avenue / street half-width, sidewalk
AVENUES = [(-101.7, RN), (-13.7, RN), (74.3, 80.0), (162.3, RN), (250.3, 80.0)]   # x and northern end
STREETS = [-178.0, -90.0, 86.0, 232.0]
t0 = (RW + 5 - diagA[0]) / dDir[0]            # the boulevard ends inside the ring at both ends
t1 = (RE + 6 - diagA[0]) / dDir[0]
road_len = t1 - t0
road_mid = diagA + dDir * (t0 + t1) / 2
ROAD_RECTS = []


def road(name, x0, y0, x1, y1):
    rect = (x0, y0, x1, y1)
    ROAD_RECTS.append(rect)
    for r in tiles(*rect):
        aabb(roads_f, name, r[0], r[1], -0.3, r[2], r[3], 0.0, ROAD, "Asphalt")
    return rect


def on_road(p, own=None, m=0.5):
    return any(r is not own and r[0] - m < p[0] < r[2] + m and r[1] - m < p[1] < r[3] + m for r in ROAD_RECTS)


def on_blvd(p, m=0.5):
    return 5.5 - m < dk(p) < 25 + m and t0 < dt(p) < t1


def off_diag(x0, y0, x1, y1, m=0.0):
    ks = [dk((x, y)) for x in (x0, x1) for y in (y0, y1)]
    return max(ks) < DLO - m or min(ks) > DHI + m


def paved(parent, name, x0, y0, x1, y1, z_top, t, color, mat):
    """A flat rectangle, less whatever of it the boulevard crosses."""
    if off_diag(x0, y0, x1, y1):
        return aabb(parent, name, x0, y0, z_top - t, x1, y1, z_top, color, mat)
    for f in (lambda p: DLO - dk(p), lambda p: dk(p) - DHI):
        piece = clip(R4(x0, y0, x1, y1), f)
        if len(piece) >= 3 and abs(area(piece)) > 0.05:
            cslab(parent, name, piece, z_top, t, color, mat)


RING = [road("Highway", RW - RH, RS - RH, RW + RH, RN + RH), road("Highway", RE - RH, RS - RH, RE + RH, RN + RH),
        road("Highway", RW + RH, RS - RH, RE - RH, RS + RH), road("Highway", RW + RH, RN - RH, RE - RH, RN + RH)]
AVE = [road("Avenue", ax - AH, RS + RH, ax + AH, RN - RH if top >= RN else top) for ax, top in AVENUES]
STR = []
for sy in STREETS:
    xs = [RW + RH] + [v for ax, top in AVENUES if sy < top for v in (ax - AH, ax + AH)] + [RE - RH]
    STR += [road("Street", xa, sy - AH, xb, sy + AH) for xa, xb in zip(xs[::2], xs[1::2])]
for i in range(2):
    a_, b_ = t0 + road_len * i / 2, t0 + road_len * (i + 1) / 2
    c = diagA + dDir * (a_ + b_) / 2 + dOut * 15.25
    ybox(roads_f, "Boulevard", c[0], c[1], -0.18, b_ - a_, 19.5, 0.2, phi_road, ROAD, "Asphalt")


def pairs(v):
    return list(zip(v[::2], v[1::2]))


xs_s = [RW + RH] + [v for ax, top in AVENUES for v in (ax - AH, ax + AH)] + [RE - RH]
xs_n = [RW + RH] + [v for ax, top in AVENUES if top >= RN for v in (ax - AH, ax + AH)] + [RE - RH]
ys_ = [RS + RH] + [v for sy in STREETS for v in (sy - AH, sy + AH)] + [RN - RH]
BLOCKS = {}
for j, (y0, y1) in enumerate(pairs(ys_)):
    north = y0 > 86
    names = ["C1", "C2", "C34", "C56"] if north else ["C1", "C2", "C3", "C4", "C5", "C6"]
    for nm, (x0, x1) in zip(names, pairs(xs_n if north else xs_s)):
        BLOCKS["%sR%d" % (nm, j + 1)] = (x0, y0, x1, y1)

for x0, y0, x1, y1 in BLOCKS.values():
    for r in ((x0, y0, x1, y0 + SW), (x0, y1 - SW, x1, y1), (x0, y0 + SW, x0 + SW, y1 - SW),
              (x1 - SW, y0 + SW, x1, y1 - SW)):
        paved(walks_f, "Sidewalk", *r, 0.1, 0.25, WALK, "Concrete")


def strip(k0, k1, ta=None, tb=None):
    ta, tb = (t0, t1) if ta is None else (ta, tb)
    return [diagA + dDir * ta + dOut * k0, diagA + dDir * tb + dOut * k0,
            diagA + dDir * tb + dOut * k1, diagA + dDir * ta + dOut * k1]


for k0, k1 in ((0.0, 5.5), (25.0, 28.0)):
    for rect in BLOCKS.values():
        piece = clip_rect(strip(k0, k1), *rect)
        if len(piece) >= 3 and abs(area(piece)) > 0.05:
            cslab(walks_f, "Pavement", piece, 0.1, 0.25, WALK, "Concrete")


def dash_line(a, b, period, length, width, color, own=None):
    a, b = np.array(a, float), np.array(b, float)
    L, u = np.linalg.norm(b - a), unit(b - a)
    phi = math.atan2(u[1], u[0])
    for s in np.arange(period / 2, L, period):
        q = a + u * s
        if on_road(q, own, 1.0) or (own is not None and on_blvd(q, 1.0)):
            continue
        ybox(roads_f, "Lane mark", q[0], q[1], 0.0, length, width, 0.012, phi, color, collide=False, shadow=False,
             query=False)


for x, own in ((RW, RING[0]), (RE, RING[1])):
    for o in (-4.6, 4.6):
        dash_line((x + o, RS), (x + o, RN), 15, 4, 0.15, MARK, own)
for y, own in ((RS, RING[2]), (RN, RING[3])):
    for o in (-4.6, 4.6):
        dash_line((RW + RH, y + o), (RE - RH, y + o), 15, 4, 0.15, MARK, own)
for (ax, top), own in zip(AVENUES, AVE):
    dash_line((ax, own[1]), (ax, own[3]), 13, 3, 0.14, YELLOW, own)
for own in STR:
    dash_line((own[0], (own[1] + own[3]) / 2), (own[2], (own[1] + own[3]) / 2), 13, 3, 0.14, YELLOW, own)
for k, period, length, color in ((10.4, 12, 3.5, MARK), (20.1, 12, 3.5, MARK), (15.25, 12, 11.6, YELLOW)):
    dash_line(diagA + dDir * t0 + dOut * k, diagA + dDir * t1 + dOut * k, period, length, 0.15, color)


def pieces(lo, hi, gaps):
    out, s = [], lo
    for g0, g1 in sorted(gaps):
        if g0 > s:
            out.append((s, min(g0, hi)))
        s = max(s, g1)
    if s < hi:
        out.append((s, hi))
    return [(a, b) for a, b in out if b - a > 1]


def blvd_y_at(x):
    ys = []
    for k in (5.5, 25.0):
        t = (x - diagA[0] - dOut[0] * k) / dDir[0]
        ys.append(diagA[1] + dDir[1] * t + dOut[1] * k)
    return min(ys), max(ys)


def ring_lamp(x, y, along):
    lp = new(city_lamps, "Model", "Highway light")
    vcyl(lp, "Pole", x, y, 0.85, 10.4, 0.3, (150, 154, 158), "Metal")
    across = np.array([-along[1], along[0]])
    head = wall(lp, "Head", np.array([x, y]) - across * 3.6, np.array([x, y]) + across * 3.6, 11.2, 0.3, 0.45,
                (255, 214, 160))
    light(head, rng=55, brightness=2.0, color=(255, 210, 150), enabled=False, name="NightLight")


for x in (RW, RE):        # the median down the ring, with gaps at every junction
    gaps = [(sy - AH - 5, sy + AH + 5) for sy in STREETS] + [tuple(np.array(blvd_y_at(x)) + (-5, 5))]
    for a_, b_ in pieces(RS, RN, gaps):
        aabb(roads_f, "Median", x - 0.3, a_, 0.0, x + 0.3, b_, 0.85, MEDIAN, "Concrete")
        for y in np.arange(a_ + 20, b_ - 10, 50):
            ring_lamp(x, y, (0, 1))
for y in (RS, RN):
    gaps = [(ax - AH - 5, ax + AH + 5) for ax, top in AVENUES if y == RS or top >= RN]
    for a_, b_ in pieces(RW + 0.3, RE - 0.3, gaps):
        aabb(roads_f, "Median", a_, y - 0.3, 0.0, b_, y + 0.3, 0.85, MEDIAN, "Concrete")
        for x in np.arange(a_ + 20, b_ - 10, 50):
            ring_lamp(x, y, (1, 0))


def street_lamp(q, toward, z0=0.1):
    lp = new(city_lamps, "Model", "Street light")
    vcyl(lp, "Pole", q[0], q[1], z0, 7.5, 0.18, (70, 74, 78), "Metal")
    toward = np.array(toward, float)
    head = wall(lp, "Head", q + toward * 0.15, q + toward * 1.7, z0 + 7.3, 0.22, 0.4, (255, 214, 160))
    light(head, rng=40, brightness=1.8, color=(255, 210, 150), enabled=False, name="NightLight")


def lamp_ok(q):
    return not on_road(q, None, 0.3) and not (DLO - 1.5 < dk(q) < DHI + 1.5) and \
        any(r[0] < q[0] < r[2] and r[1] < q[1] < r[3] for r in BLOCKS.values())


for n_, own in enumerate(AVE):
    for i, y in enumerate(np.arange(own[1] + 14, own[3] - 6, 40)):
        side = (i + n_) % 2
        q = np.array([own[0] - 0.9, y]) if side == 0 else np.array([own[2] + 0.9, y])
        if lamp_ok(q):
            street_lamp(q, (1, 0) if side == 0 else (-1, 0))
for n_, own in enumerate(STR):
    for i, x in enumerate(np.arange(own[0] + 14, own[2] - 6, 40)):
        side = (i + n_) % 2
        q = np.array([x, own[1] - 0.9]) if side == 0 else np.array([x, own[3] + 0.9])
        if lamp_ok(q):
            street_lamp(q, (0, 1) if side == 0 else (0, -1))
for s in np.arange(t0 + 12, t1 - 6, 36):          # far pavement of the boulevard
    q = diagA + dDir * s + dOut * 26.4
    if not on_road(q, None, 1.0):
        street_lamp(q, -dOut)

# ---- the mall's own frontage on the boulevard (as before)
wall(ground, "Feature wall", P(830, 876), P(1180, 1045), 0.0, 1.2, 0.9, (214, 218, 220), "Metal")
wall(ground, "Feature wall light", P(830, 876), P(1180, 1045), 1.2, 0.06, 0.95, (120, 230, 255), "Neon", collide=False)
sign_part = wall(ground, "Mall sign", P(1060, 900), P(1180, 957), 1.26, 0.9, 0.3, (24, 26, 30))
sign_part = sign(sign_part, "GLASS MALL", face="Back")

trees = new(site, "Folder", "Trees")
SPECIES = [[(94, 127, 57), (111, 143, 69), (82, 111, 49)], [(75, 106, 48), (88, 122, 55), (98, 132, 61)],
           [(216, 71, 29), (232, 93, 36), (93, 124, 53)], [(228, 141, 179), (240, 166, 197), (107, 138, 66)]]
spots = []
for i, s in enumerate(np.arange(-20, 125, 11)):
    spots.append((diagA + dDir * s + dOut * 3, 9, 3.4, 2 if i % 3 == 1 else 0))
for px, py in ((700, 760), (760, 790), (880, 770), (1270, 800), (1330, 860), (1300, 960), (1360, 1060), (600, 400),
               (600, 520), (600, 640), (1440, 420), (1440, 560), (1440, 700), (1440, 860), (1440, 1000), (700, 300),
               (850, 300), (1000, 300), (1150, 300), (1300, 300)):
    spots.append((P(px, py), 7 + rnd.random() * 4, 2.6 + rnd.random() * 1.4, rnd.choice([0, 1, 0, 1, 2, 3])))
for q, h, rr, sp in spots:
    if not on_road(q, None, 1.5) and not on_blvd(q, 1.0):
        tree(trees, q, h, rr, SPECIES[sp], n=6)
for s in np.arange(t0 + 30, t1 - 10, 24):         # boulevard trees on the far pavement
    q = diagA + dDir * s + dOut * 27.0
    if not on_road(q, None, 2.5):
        tree(trees, q, 8 + rnd.random() * 3, 3.0, SPECIES[rnd.choice([0, 1, 2])])

lamps = new(site, "Folder", "StreetLights")
for s in np.arange(t0 + 6, t1 - 6, 16):
    if not -30 <= s < 140 and (s - t0) % 32 > 16:      # every 16 m past the mall, 32 m elsewhere
        continue
    q = diagA + dDir * s + dOut * 5.2
    if on_road(q, None, 1.0):
        continue
    lp = new(lamps, "Model", "Street light")
    vcyl(lp, "Pole", q[0], q[1], 0.1, 8.0, 0.18, (70, 74, 78), "Metal")
    hq = q + dOut * 0.7
    head = aabb(lp, "Head", hq[0] - 0.7, hq[1] - 0.2, 7.9, hq[0] + 0.7, hq[1] + 0.2, 8.15, (255, 214, 160))
    light(head, rng=40, brightness=2.2, color=(255, 210, 150), enabled=False, name="NightLight")

for s in (-10, 20, 50, 80, 110):
    q = diagA + dDir * s + dOut * 2.6
    aabb(wp_street, "Street", q[0] - 0.2, q[1] - 0.2, 0.5, q[0] + 0.2, q[1] + 0.2, 0.9, (255, 0, 0), tr=1,
         collide=False, query=False, shadow=False)
aabb(wp_street, "Street", -3.6, 51.0, 0.4, -3.2, 51.4, 0.8, (255, 0, 0), tr=1, collide=False, query=False, shadow=False)

# ---- coins, parked cars, car pads and portals: what the scripts read
RESERVED = []
COIN_SPOTS = []


def coin(x, y, z=1.0):
    COIN_SPOTS.append((x, y, z))
    c = mbox(coins_f, "Coin", (x, y, z), UP, (0.3, 1.6, 1.6), (255, 196, 40), "Neon", shape=2, collide=False,
             shadow=False, query=False)
    c.props["CanTouch"] = ("bool", True)


def marker(parent, name, x, y, z, heading):
    """An invisible spot a car is built on, nose towards heading (radians, model space)."""
    return ybox(parent, name, x, y, z + 0.05, 2.0, 4.6, 0.3, heading - math.pi / 2, (255, 0, 0), tr=1, collide=False,
                query=False, shadow=False)


def parked(x, y, z, heading):
    marker(spawns_f, "Parked", x, y, z, heading)


def car_pad(x, y, z, sx, sy, heading):
    """A glowing "Get a car" pad at (x, y); the car appears at (sx, sy) facing heading."""
    m = new(spawns_f, "Model", "Pad")
    base = vcyl(m, "Base", x, y, z, 0.08, 3.6, (60, 220, 255), "Neon", tr=0.25, collide=False, shadow=False)
    new(base, "ProximityPrompt", "Prompt", ActionText=("string", "Get a car"), ObjectText=("string", "Car pad"),
        HoldDuration=("float", 0.25), MaxActivationDistance=("float", 12), RequiresLineOfSight=("bool", False))
    vcyl(m, "Beacon", x, y, z + 0.08, 3.0, 0.25, (60, 220, 255), "Neon", tr=0.4, collide=False, shadow=False)
    marker(m, "SpawnPoint", sx, sy, z, heading)
    RESERVED.append((min(x, sx) - 3.5, min(y, sy) - 3.5, max(x, sx) + 3.5, max(y, sy) + 3.5))


def portal(name, x, y, z, target, label):
    p = vcyl(portals_f, name, x, y, z, 0.08, 3.4, (190, 90, 255), "Neon", tr=0.2, collide=False, shadow=False)
    values(p, Target=target, Label=label)


def fits(x0, y0, x1, y1, m=3.0):
    return off_diag(x0, y0, x1, y1, m) and not any(
        x0 < r[2] and r[0] < x1 and y0 < r[3] and r[1] < y1 for r in RESERVED)


def lots(x0, y0, x1, y1, cell, gap=4.0):
    """Building plots of about cell metres inside a block's sidewalks."""
    ix0, iy0, ix1, iy1 = x0 + SW + gap, y0 + SW + gap, x1 - SW - gap, y1 - SW - gap
    nx, ny = max(1, int((ix1 - ix0) // cell)), max(1, int((iy1 - iy0) // cell))
    cw, ch = (ix1 - ix0) / nx, (iy1 - iy0) / ny
    for i in range(nx):
        for j in range(ny):
            yield ix0 + cw * i, iy0 + ch * j, ix0 + cw * (i + 1), iy0 + ch * (j + 1)


# ---- rooms and furniture: what every building's interior is made of
class Room:
    """A rectangle of floor seen from its front: u runs across it (+u is on your right, seen from
    the street), v runs in from the front face, z is the floor top; f is the front's outward normal."""

    def __init__(self, x0, y0, x1, y1, front, z):
        self.f = np.array(front, float)
        self.a = np.array([-self.f[1], self.f[0]])
        self.z = z
        self.W, self.D = (y1 - y0, x1 - x0) if abs(self.f[0]) > 0.5 else (x1 - x0, y1 - y0)
        self.o = np.array([(x0 + x1) / 2, (y0 + y1) / 2]) + self.f * self.D / 2

    def p(self, u, v):
        return self.o + self.a * u - self.f * v

    def box(self, par, name, u0, v0, u1, v1, z0, z1, color, mat="SmoothPlastic", **kw):
        p, q = self.p(u0, v0), self.p(u1, v1)
        return aabb(par, name, min(p[0], q[0]), min(p[1], q[1]), self.z + z0, max(p[0], q[0]), max(p[1], q[1]),
                    self.z + z1, color, mat, **kw)

    def phi(self, du, dv):
        g = self.a * du - self.f * dv
        return math.atan2(-g[0], g[1])

    def obj(self, par, name, u, v, z0, w, d, h, face, color, mat="SmoothPlastic", **kw):
        """A box w across, d deep and h tall at (u, v), its Front face towards face (du, dv)."""
        q = self.p(u, v)
        return ybox(par, name, q[0], q[1], self.z + z0, w, d, h, self.phi(*face), color, mat, **kw)

    def at(self, u, v, face, ahead=0.0, side=0.0):
        du, dv = face
        return u + du * ahead + dv * side, v + dv * ahead - du * side

    def sub(self, u0, v0, u1, v1, front=None, z=None):
        """A smaller room inside this one, by its corners in this room's (u, v)."""
        p, q = self.p(u0, v0), self.p(u1, v1)
        return Room(min(p[0], q[0]), min(p[1], q[1]), max(p[0], q[0]), max(p[1], q[1]),
                    self.f if front is None else front, self.z if z is None else z)


SIDES = ("front", "back", "left", "right")
GLAZING = dict(color=(170, 205, 215), mat="Glass", tr=0.5, refl=0.06, shadow=False)


def side_box(R, par, name, side, s0, s1, z0, z1, t, color, mat="SmoothPlastic", inset=0.0, **kw):
    """A piece of the wall on one side of R; s runs along it (u for front and back, v for the sides)."""
    W, D, i0, i1 = R.W, R.D, inset, t - inset
    if side == "front":
        return R.box(par, name, s0, i0, s1, i1, z0, z1, color, mat, **kw)
    if side == "back":
        return R.box(par, name, s0, D - i1, s1, D - i0, z0, z1, color, mat, **kw)
    if side == "left":
        return R.box(par, name, -W / 2 + i0, s0, -W / 2 + i1, s1, z0, z1, color, mat, **kw)
    return R.box(par, name, W / 2 - i1, s0, W / 2 - i0, s1, z0, z1, color, mat, **kw)


def owall(R, par, side, z0, z1, t, color, mat, opens=(), glass=None, name="Wall"):
    """One wall of R from z0 to z1 with openings (centre, width, bottom, top, kind): "door" leaves
    a gap, "window" fills it with glass."""
    glass = glass or GLAZING
    s0, s1 = (-R.W / 2, R.W / 2) if side in ("front", "back") else (t, R.D - t)
    cuts = sorted({s0, s1} | {min(max(o[0] + e * o[1] / 2, s0), s1) for o in opens for e in (-1, 1)})
    for sa, sb in zip(cuts, cuts[1:]):
        if sb - sa < 1e-3:
            continue
        mid = (sa + sb) / 2
        z = z0
        for zb, zt, kind in sorted((o[2], o[3], o[4]) for o in opens if o[0] - o[1] / 2 <= mid <= o[0] + o[1] / 2):
            if zb > z + 1e-3:
                side_box(R, par, name, side, sa, sb, z, zb, t, color, mat)
            if kind == "window":
                side_box(R, par, "Window", side, sa, sb, max(z, zb), zt, t, inset=t / 2 - 0.03, **glass)
            z = max(z, zt)
        if z1 > z + 1e-3:
            side_box(R, par, name, side, sa, sb, z, z1, t, color, mat)


def opening_ends(R, side, c, w, t):
    """The ends of an opening's centre line, ordered so a wall built from one to the other faces out."""
    if side == "front":
        return R.p(c - w / 2, t / 2), R.p(c + w / 2, t / 2)
    if side == "back":
        return R.p(c + w / 2, R.D - t / 2), R.p(c - w / 2, R.D - t / 2)
    if side == "left":
        return R.p(-R.W / 2 + t / 2, c + w / 2), R.p(-R.W / 2 + t / 2, c - w / 2)
    return R.p(R.W / 2 - t / 2, c - w / 2), R.p(R.W / 2 - t / 2, c + w / 2)


def swing_door(par, R, side, c, w, t, color=(120, 80, 50)):
    """A hinged door that swings in when someone comes close (Doors.server)."""
    m = new(par, "Model", "SwingDoor")
    a, b = opening_ends(R, side, c, w, t)
    wall(m, "Leaf", a, b, R.z, 2.1, 0.06, color, "Wood")
    wall(m, "Handle", b - unit(b - a) * 0.12, b - unit(b - a) * 0.08, R.z + 0.95, 0.06, 0.16, (210, 190, 120), "Metal",
         collide=False)


def glass_door(par, R, side, c, w, t, h=2.6):
    a, b = opening_ends(R, side, c, w, t)
    auto_door(par, a, b, R.z, h=h, out=0.0)


def lamp_panel(R, par, u, v, zc, w=0.9, d=0.9, rng=16, brightness=0.75, color=(255, 240, 220), lit=True):
    p = R.box(par, "Ceiling light", u - w / 2, v - d / 2, u + w / 2, v + d / 2, zc - 0.04, zc, (255, 248, 236), "Neon",
              collide=False, shadow=False)
    if lit:
        light(p, rng=rng, brightness=brightness, color=color)
    return p


def pendant(R, par, u, v, zc, drop=1.2, color=(255, 214, 150), lit=False):
    q = R.p(u, v)
    vcyl(par, "Pendant cord", q[0], q[1], R.z + zc - drop, drop, 0.02, (30, 30, 32), collide=False)
    g = ball(par, "Pendant", q[0], q[1], R.z + zc - drop - 0.12, 0.3, color, "Neon", collide=False, shadow=False)
    if lit:
        light(g, rng=12, brightness=0.6, color=color)


def rug(R, par, u, v, w, d, color):
    R.box(par, "Rug", u - w / 2, v - d / 2, u + w / 2, v + d / 2, 0.0, 0.025, color, "Fabric", collide=False)


def sofa(R, par, u, v, face, w=2.2, color=(110, 120, 140)):
    R.obj(par, "Sofa", u, v, 0, w, 0.9, 0.4, face, color, "Fabric")
    bu, bv = R.at(u, v, face, -0.35)
    R.obj(par, "Sofa back", bu, bv, 0.4, w, 0.2, 0.5, face, color, "Fabric")
    for e in (-1, 1):
        au, av = R.at(u, v, face, 0.0, e * (w / 2 - 0.1))
        R.obj(par, "Sofa arm", au, av, 0.4, 0.2, 0.9, 0.22, face, color, "Fabric")
    su, sv = R.at(u, v, face, 0.08)
    st = R.obj(par, "Seat", su, sv, 0.4, w - 0.5, 0.6, 0.08, face, tuple(min(255, c + 22) for c in color), "Fabric",
               cls="Seat")
    st.props["Disabled"] = ("bool", False)


def chair(R, par, u, v, face, color=(150, 104, 66)):
    q = R.p(u, v)
    return seat(par, q[0], q[1], R.z, R.phi(*face), color=color, back=True, w=0.48)


def stool(R, par, u, v, color=(200, 60, 50), h=0.78):
    q = R.p(u, v)
    vcyl(par, "Stool leg", q[0], q[1], R.z, h - 0.06, 0.09, (60, 62, 66), "Metal")
    st = mbox(par, "Seat", (q[0], q[1], R.z + h - 0.03), UP, (0.42, 0.06, 0.42), color, "Fabric", cls="Seat")
    st.props["Disabled"] = ("bool", False)


def table(R, par, u, v, w, d, color=(150, 104, 66), h=0.75, mat="Wood"):
    R.box(par, "Table", u - w / 2, v - d / 2, u + w / 2, v + d / 2, h - 0.05, h, color, mat)
    if max(w, d) < 1.3:
        R.box(par, "Table leg", u - 0.07, v - 0.07, u + 0.07, v + 0.07, 0, h - 0.05, (60, 62, 66), "Metal")
    elif w >= d:
        for e in (-1, 1):
            R.box(par, "Table leg", u + e * (w / 2 - 0.3) - 0.05, v - d / 2 + 0.15, u + e * (w / 2 - 0.3) + 0.05,
                  v + d / 2 - 0.15, 0, h - 0.05, (60, 62, 66), "Metal")
    else:
        for e in (-1, 1):
            R.box(par, "Table leg", u - w / 2 + 0.15, v + e * (d / 2 - 0.3) - 0.05, u + w / 2 - 0.15,
                  v + e * (d / 2 - 0.3) + 0.05, 0, h - 0.05, (60, 62, 66), "Metal")


def dining(R, par, u, v, w=1.6, d=0.9, n=4, color=(150, 104, 66), chairs=(60, 62, 66), cloth=None):
    table(R, par, u, v, w, d, cloth or color, mat="Fabric" if cloth else "Wood")
    per = max(1, n // 2)
    for k in range(per):
        x = u - w / 2 + w * (k + 0.5) / per
        chair(R, par, x, v - d / 2 - 0.42, (0, 1), chairs)
        chair(R, par, x, v + d / 2 + 0.42, (0, -1), chairs)


def bed(R, par, u, v, face, w=1.6, L=2.1, color=(70, 90, 140), frame=(120, 90, 64)):
    """(u, v) is the bed's middle; face points from its head to its foot."""
    R.obj(par, "Bed", u, v, 0, w, L, 0.35, face, frame, "Wood")
    R.obj(par, "Mattress", u, v, 0.35, w - 0.08, L - 0.1, 0.2, face, (245, 245, 240), "Fabric")
    fu, fv = R.at(u, v, face, 0.25)
    R.obj(par, "Duvet", fu, fv, 0.55, w - 0.02, L * 0.66, 0.07, face, color, "Fabric")
    hu, hv = R.at(u, v, face, -L / 2 + 0.05)
    R.obj(par, "Headboard", hu, hv, 0, w + 0.1, 0.1, 1.1, face, frame, "Wood")
    pu, pv = R.at(u, v, face, -L / 2 + 0.38)
    R.obj(par, "Pillow", pu, pv, 0.55, w - 0.4, 0.4, 0.14, face, WHITE, "Fabric")


def tv(R, par, u, v, face, w=1.4, text="GLASS CITY TV", accent=(60, 200, 255)):
    R.obj(par, "TV unit", u, v, 0, w + 0.5, 0.45, 0.5, face, (60, 50, 44), "Wood")
    s = R.obj(par, "TV", u, v, 0.62, w, 0.06, w * 0.56, face, (12, 12, 14), refl=0.2)
    sign(s, text, face="Front", style="screen", accent=accent)


def floor_lamp(R, par, u, v, color=(255, 236, 200)):
    q = R.p(u, v)
    vcyl(par, "Lamp pole", q[0], q[1], R.z, 1.5, 0.05, (60, 62, 66), "Metal")
    shade = vcyl(par, "Lamp shade", q[0], q[1], R.z + 1.42, 0.36, 0.46, color, "Neon", collide=False, shadow=False)
    light(shade, rng=11, brightness=0.55, color=(255, 220, 170))


def plant(R, par, u, v, h=1.1, pot=(196, 108, 72)):
    q = R.p(u, v)
    vcyl(par, "Pot", q[0], q[1], R.z, 0.45, 0.5, pot, "Concrete")
    ball(par, "Plant", q[0], q[1], R.z + 0.45 + h * 0.38, h * 0.78, rnd.choice(SPECIES[0] + SPECIES[1]), "Grass",
         collide=False)


BOOKS = [(180, 60, 50), (60, 110, 170), (220, 180, 60), (70, 140, 90), (230, 226, 214), (120, 70, 140), (40, 44, 52)]


def shelf(R, par, u, v, face, w=1.6, h=2.0, color=(150, 104, 66), stock=BOOKS, rows=4):
    R.obj(par, "Shelf", u, v, 0, w, 0.36, h, face, color, "Wood")
    fu, fv = R.at(u, v, face, 0.16)
    for k in range(rows):
        z = 0.3 + k * (h - 0.4) / rows
        R.obj(par, "Shelf stock", fu, fv, z, w - 0.14, 0.07, (h - 0.4) / rows * 0.7, face, rnd.choice(stock),
              collide=False)


def counter(R, par, u0, v0, u1, v1, color=(240, 240, 236), top=(60, 62, 66), h=0.95, mat="Wood", top_mat="Marble"):
    R.box(par, "Counter", u0, v0, u1, v1, 0, h - 0.05, color, mat)
    R.box(par, "Worktop", u0 - 0.03, v0 - 0.03, u1 + 0.03, v1 + 0.03, h - 0.05, h, top, top_mat)


ART = [(230, 90, 70), (240, 190, 60), (70, 140, 210), (90, 180, 140), (200, 90, 160), (30, 34, 40), (240, 236, 228),
       (250, 140, 60), (120, 200, 220)]


def painting(R, par, u, v, face, w=1.2, h=0.9, z=1.3):
    R.obj(par, "Frame", u, v, z, w + 0.1, 0.05, h + 0.1, face, (30, 28, 26), "Wood")
    fu, fv = R.at(u, v, face, 0.03)
    c1, c2 = rnd.sample(ART, 2)
    R.obj(par, "Canvas", fu, fv, z + 0.05, w, 0.02, h, face, c1, collide=False)
    su, sv = R.at(fu, fv, face, 0.012, rnd.uniform(-w / 4, w / 4))
    R.obj(par, "Canvas", su, sv, z + 0.05 + h * rnd.uniform(0.12, 0.4), w * rnd.uniform(0.25, 0.5), 0.02,
          h * rnd.uniform(0.3, 0.5), face, c2, collide=False)


def desk(R, par, u, v, face, w=1.4, color=(240, 240, 236), screen=(40, 110, 170)):
    """face points from the chair to the screen."""
    back = (-face[0], -face[1])
    R.obj(par, "Desk", u, v, 0.7, w, 0.7, 0.04, face, color, "Wood")
    pu, pv = R.at(u, v, face, 0.3)
    R.obj(par, "Desk panel", pu, pv, 0, w - 0.1, 0.04, 0.7, face, (80, 82, 86), "Metal")
    mu, mv = R.at(u, v, face, 0.18)
    R.obj(par, "Monitor", mu, mv, 0.78, 0.6, 0.04, 0.36, back, screen, "Neon", shadow=False)
    cu, cv = R.at(u, v, face, -0.62)
    chair(R, par, cu, cv, face, (40, 44, 52))
    return back


def fridge(R, par, u, v, face, color=(230, 232, 234)):
    R.obj(par, "Fridge", u, v, 0, 0.8, 0.7, 1.9, face, color, "Metal", refl=0.1)


def kitchen_run(R, par, u0, u1, v_wall, toward, color=(240, 240, 236), top=(60, 62, 66)):
    """Base units along u from u0 to u1, their backs on the wall at v_wall, facing toward (+1/-1 in v)."""
    va, vb = (v_wall, v_wall + 0.65 * toward)
    counter(R, par, u0, min(va, vb), u1, max(va, vb), color, top)
    R.box(par, "Hob", u0 + 0.4, min(va, vb) + 0.1, u0 + 1.0, max(va, vb) - 0.1, 0.95, 0.965, (20, 20, 22), "Glass",
          collide=False)
    R.box(par, "Sink", u1 - 1.1, min(va, vb) + 0.12, u1 - 0.5, max(va, vb) - 0.12, 0.95, 0.96, (180, 184, 188), "Metal",
          collide=False)
    wa, wb = v_wall, v_wall + 0.35 * toward
    R.box(par, "Wall cupboard", u0, min(wa, wb), u1, max(wa, wb), 1.55, 2.25, color, "Wood")


def plinth(R, par, u, v, w=0.6, h=1.0, color=(240, 238, 232)):
    R.box(par, "Plinth", u - w / 2, v - w / 2, u + w / 2, v + w / 2, 0, h, color, "Marble")
    return h


def sculpture(R, par, u, v, z):
    q = R.p(u, v)
    c = rnd.choice(ART)
    k = rnd.randint(0, 2)
    if k == 0:
        ball(par, "Sculpture", q[0], q[1], R.z + z + 0.35, 0.7, c, "Metal", refl=0.3)
    elif k == 1:
        vcyl(par, "Sculpture", q[0], q[1], R.z + z, 1.1, 0.35, c, "Marble")
        ball(par, "Sculpture", q[0], q[1], R.z + z + 1.25, 0.45, rnd.choice(ART), "Metal", refl=0.3)
    else:
        R.obj(par, "Sculpture", u, v, z, 0.5, 0.5, 0.9, (math.cos(rnd.random() * 6), math.sin(rnd.random() * 6)), c,
              "Glass", refl=0.2)


def neon_strip(R, par, u0, v0, u1, v1, z, color, h=0.05):
    R.box(par, "Neon strip", u0, v0, u1, v1, z, z + h, color, "Neon", collide=False, shadow=False)


def screen_sign(R, par, u, v, face, w, h, z, text, accent=(60, 200, 255), style="screen"):
    s = R.obj(par, "Screen", u, v, z, w, 0.08, h, face, (18, 26, 60), "Neon")
    sign(s, text, face="Front", style=style, accent=accent)
    return s


def name_board(R, par, u, v, face, w, z, text, color=(28, 30, 34), h=0.6):
    s = R.obj(par, "Sign", u, v, z, w, 0.12, h, face, color)
    sign(s, text, face="Front")
    return s



# ---- what goes inside: a theme fills a ground floor R (inside its walls) whose entrance is in the
# middle of the front and whose lift core sits in the middle of the back. Themes keep the strip
# |u| < CLEAR free so you can walk from the door to the lift.
CLEAR = 2.0


def zones(R):
    """The two strips either side of the entrance-to-lift walk: (u0, u1) each, and the usable depth."""
    return (-R.W / 2 + 0.35, -CLEAR), (CLEAR, R.W / 2 - 0.35), (0.6, R.D - 0.5)


def grid(u0, u1, v0, v1, du, dv, cap=None):
    nu, nv = max(1, int((u1 - u0) // du)), max(1, int((v1 - v0) // dv))
    pts = [(u0 + (u1 - u0) * (i + 0.5) / nu, v0 + (v1 - v0) * (j + 0.5) / nv) for i in range(nu) for j in range(nv)]
    return thin(pts, cap)


def thin(items, n):
    """At most n of items, spread evenly through the list."""
    items = list(items)
    return items if n is None or len(items) <= n else [items[int(i * len(items) / n)] for i in range(n)]


def along(a, b, step, cap):
    return thin(np.arange(a, b, step), cap)


def ceiling_lights(R, par, h, n=2):
    for k in range(n):
        lamp_panel(R, par, 0.0, R.D * (k + 0.5) / n, h, w=1.4, d=0.5, rng=22, brightness=0.8)


def t_cafe(R, par, name, accent, h, menu="ESPRESSO · CHAI · FILTER KAAPI · CAKES"):
    (l0, l1), (r0, r1), (v0, v1) = zones(R)
    counter(R, par, r1 - 0.7, v1 * 0.35, r1, v1 - 0.4, (150, 104, 66), (230, 226, 218))
    cu = r1 - 0.35
    R.obj(par, "Espresso machine", cu, v1 * 0.5, 0.95, 0.6, 0.45, 0.45, (-1, 0), (200, 204, 208), "Metal", refl=0.2)
    R.obj(par, "Pastry case", cu, v1 * 0.72, 0.95, 0.5, 1.1, 0.45, (-1, 0), (200, 230, 240), "Glass", tr=0.4)
    for k, c in enumerate(((240, 190, 120), (200, 110, 80), (250, 230, 200))):
        R.obj(par, "Cake", cu, v1 * 0.72 - 0.3 + k * 0.3, 1.0, 0.22, 0.22, 0.14, (-1, 0), c, collide=False)
    screen_sign(R, par, R.W / 2 - 0.12, v1 * 0.6, (-1, 0), 2.6, 0.9, 1.9, menu, accent)
    for k, (u, v) in enumerate(grid(l0, l1, v0 + 0.4, v1 - 0.3, 2.6, 2.8, cap=9)):
        table(R, par, u, v, 0.75, 0.75, (240, 236, 228), mat="Marble")
        chair(R, par, u - 0.62, v, (1, 0), accent)
        chair(R, par, u + 0.62, v, (-1, 0), accent)
        if k % 2 == 0:
            pendant(R, par, u, v, h, 1.3, (255, 214, 150))
    for u in (r0 + 0.6, r0 + 2.0):
        if u < r1 - 1.5:
            table(R, par, u, v0 + 1.2, 0.7, 0.7, (240, 236, 228), mat="Marble")
            stool(R, par, u, v0 + 0.5, accent)
    for u, v in grid(r0 + 0.4, r1 - 1.8, v0 + 2.6, v1 - 0.8, 2.6, 2.8, cap=4):
        table(R, par, u, v, 0.75, 0.75, (240, 236, 228), mat="Marble")
        chair(R, par, u, v - 0.62, (0, 1), accent)
        chair(R, par, u, v + 0.62, (0, -1), accent)
    plant(R, par, l0 + 0.4, v0, 1.3)
    plant(R, par, r1 - 0.4, v0, 1.3)
    ceiling_lights(R, par, h)


def t_restaurant(R, par, name, accent, h):
    (l0, l1), (r0, r1), (v0, v1) = zones(R)
    for u0, u1 in ((l0, l1), (r0, r1 - 1.2)):
        for u, v in grid(u0, u1, v0 + 0.5, v1 - 0.6, 3.0, 3.0, cap=6):
            dining(R, par, u, v, 1.2, 0.85, 2, chairs=(110, 40, 40), cloth=(246, 244, 238))
            q = R.p(u, v)
            ball(par, "Candle", q[0], q[1], R.z + 0.82, 0.1, (255, 190, 90), "Neon", collide=False, shadow=False)
    counter(R, par, r1 - 0.8, v1 * 0.25, r1, v1 * 0.75, (60, 40, 30), (40, 40, 44))
    shelf(R, par, R.W / 2 - 0.25, v1 * 0.5, (-1, 0), w=v1 * 0.4, h=2.2, color=(40, 30, 26),
          stock=[(140, 40, 50), (200, 170, 90), (90, 120, 60)], rows=4)
    for k in range(3):
        pendant(R, par, 0.0, R.D * (k + 1) / 4, h, 1.0, (255, 200, 140), lit=k == 1)
    plant(R, par, l0 + 0.4, v1, 1.6)
    ceiling_lights(R, par, h)


def t_bank(R, par, name, accent, h):
    (l0, l1), (r0, r1), (v0, v1) = zones(R)
    vb = R.D * 0.62
    for u0, u1 in ((l0, l1), (r0, r1)):
        counter(R, par, u0, vb, u1, vb + 0.8, (60, 70, 86), (230, 228, 222), h=1.05)
        R.box(par, "Teller glass", u0, vb - 0.04, u1, vb, 1.05, 2.1, (190, 220, 230), "Glass", tr=0.55, shadow=False)
        for u in along(u0 + 0.8, u1 - 0.4, 1.8, 5):
            chair(R, par, u, vb + 1.3, (0, -1), (40, 44, 52))
            R.obj(par, "Monitor", u, vb + 0.55, 1.05, 0.5, 0.04, 0.32, (0, -1), (40, 110, 170), "Neon", shadow=False)
    R.obj(par, "Vault door", l0 + 0.1, R.D * 0.85, 0.2, 2.0, 0.25, 2.0, (1, 0), (170, 174, 180), "DiamondPlate")
    R.obj(par, "Vault wheel", l0 + 0.25, R.D * 0.85, 1.1, 0.7, 0.08, 0.12, (1, 0), (220, 190, 110), "Metal")
    for e in (-1, 1):
        sofa(R, par, e * (R.W / 4 + 0.5), 2.2, (0, 1), w=2.0, color=(60, 70, 86))
    R.obj(par, "ATM", r1 - 0.3, 1.0, 0, 0.8, 0.6, 1.7, (-1, 0), (50, 54, 60), "Metal")
    R.obj(par, "ATM screen", r1 - 0.62, 1.0, 1.1, 0.4, 0.02, 0.3, (-1, 0), (60, 200, 140), "Neon")
    name_board(R, par, 0.0, R.D - 0.3, (0, -1), 3.4, h - 1.0, name, (20, 40, 80))
    plant(R, par, l0 + 0.4, v0, 1.4)
    plant(R, par, r1 - 0.4, v0 + 2.5, 1.4)
    ceiling_lights(R, par, h, 3)


def t_gym(R, par, name, accent, h):
    (l0, l1), (r0, r1), (v0, v1) = zones(R)
    for u in along(l0 + 0.6, l1 - 0.3, 1.3, 7):
        R.obj(par, "Treadmill", u, v0 + 1.4, 0, 0.8, 1.9, 0.22, (0, -1), (40, 42, 46), "Metal")
        cu, cv = u, v0 + 0.55
        R.obj(par, "Treadmill post", cu, cv, 0.22, 0.7, 0.08, 1.0, (0, -1), (120, 124, 130), "Metal")
        R.obj(par, "Treadmill screen", cu, cv, 1.22, 0.6, 0.12, 0.3, (0, 1), accent, "Neon", shadow=False)
    rug(R, par, (l0 + l1) / 2, v1 - 2.6, l1 - l0 - 0.4, 4.0, (40, 40, 44))
    for u in along(l0 + 0.8, l1 - 0.6, 1.8, 5):
        q = R.p(u, v1 - 1.6)
        vcyl(par, "Punch bag", q[0], q[1], R.z + 0.6, 1.2, 0.45, (170, 40, 40), "Fabric")
        vcyl(par, "Chain", q[0], q[1], R.z + 1.8, h - 1.8, 0.04, (90, 92, 96), "Metal", collide=False)
    for v in along(v0 + 1.0, v1 - 1.0, 2.6, 6):
        R.obj(par, "Bench", r0 + 1.2, v, 0, 0.45, 1.3, 0.45, (0, 1), (30, 32, 36), "Fabric")
        R.obj(par, "Rack", r0 + 1.2, v - 0.75, 0, 1.6, 0.25, 1.6, (0, 1), (90, 94, 100), "Metal")
        R.obj(par, "Barbell", r0 + 1.2, v - 0.7, 1.35, 1.9, 0.06, 0.06, (0, 1), (200, 204, 208), "Metal")
    R.box(par, "Mirror", R.W / 2 - 0.08, v0, R.W / 2 - 0.04, v1, 0.3, 2.4, (210, 220, 226), "Glass", refl=0.6)
    R.box(par, "Dumbbell rack", r1 - 0.7, v1 * 0.3, r1 - 0.2, v1 * 0.7, 0, 0.8, (60, 62, 66), "Metal")
    name_board(R, par, 0.0, R.D - 0.3, (0, -1), 3.2, h - 1.0, name, (30, 30, 34))
    neon_strip(R, par, -R.W / 2 + 0.3, R.D - 0.25, R.W / 2 - 0.3, R.D - 0.2, h - 0.25, accent)
    ceiling_lights(R, par, h, 3)


def t_gallery(R, par, name, accent, h):
    (l0, l1), (r0, r1), (v0, v1) = zones(R)
    for v in along(v0 + 1.2, v1 - 0.8, 3.0, 8):
        painting(R, par, -R.W / 2 + 0.12, v, (1, 0), w=1.6, h=1.2, z=1.0)
        painting(R, par, R.W / 2 - 0.12, v, (-1, 0), w=1.6, h=1.2, z=1.0)
    for u0, u1 in ((l0 + 1.2, l1), (r0, r1 - 1.2)):
        for u, v in grid(u0, u1, v0 + 1.0, v1 - 1.0, 3.4, 3.6, cap=5):
            sculpture(R, par, u, v, plinth(R, par, u, v))
    R.obj(par, "Bench", 0.0, R.D * 0.45, 0, 0.6, 2.0, 0.45, (1, 0), (40, 40, 44), "Wood")
    for k in range(4):
        lamp_panel(R, par, 0.0, R.D * (k + 0.5) / 4, h, w=0.5, d=R.D / 5, rng=16, brightness=0.6, lit=k % 2 == 0)


def t_books(R, par, name, accent, h):
    (l0, l1), (r0, r1), (v0, v1) = zones(R)
    for v in along(v0 + 1.0, v1 - 0.6, 2.0, 9):
        shelf(R, par, -R.W / 2 + 0.25, v, (1, 0), w=1.8, h=2.3, rows=3)
        shelf(R, par, R.W / 2 - 0.25, v, (-1, 0), w=1.8, h=2.3, rows=3)
    for u in ((l0 + l1) / 2 + 0.6, (r0 + r1) / 2 - 0.6):
        table(R, par, u, R.D * 0.35, 1.6, 0.9, (150, 104, 66))
        for k in range(4):
            R.box(par, "Book stack", u - 0.6 + k * 0.38, R.D * 0.35 - 0.2, u - 0.4 + k * 0.38, R.D * 0.35 + 0.1, 0.75,
                  0.75 + 0.06 * (k + 1), rnd.choice(BOOKS), collide=False)
    rug(R, par, (l0 + l1) / 2 + 0.6, R.D * 0.7, 3.2, 2.6, (150, 60, 50))
    sofa(R, par, (l0 + l1) / 2 + 0.6, R.D * 0.7 + 0.6, (0, -1), w=1.8, color=(70, 90, 70))
    floor_lamp(R, par, (l0 + l1) / 2 - 0.8, R.D * 0.7 + 0.9)
    counter(R, par, r0 + 0.5, R.D * 0.65, r1 - 0.8, R.D * 0.65 + 0.7, (150, 104, 66), (230, 226, 218))
    ceiling_lights(R, par, h)


def t_tech(R, par, name, accent, h):
    (l0, l1), (r0, r1), (v0, v1) = zones(R)
    for u0, u1 in ((l0 + 0.3, l1 - 0.3), (r0 + 0.3, r1 - 0.3)):
        for v in along(v0 + 1.2, v1 - 1.0, 3.2, 4):
            u = (u0 + u1) / 2
            R.box(par, "Display table", u - (u1 - u0) / 2, v - 0.5, u + (u1 - u0) / 2, v + 0.5, 0, 0.9, (236, 236, 232),
                  "Wood")
            for x in along(u0 + 0.4, u1 - 0.2, 1.1, 6):
                R.box(par, "Device", x - 0.18, v - 0.12, x + 0.18, v + 0.12, 0.9, 0.93, (20, 20, 24), "Glass",
                      collide=False)
                R.box(par, "Device screen", x - 0.16, v - 0.1, x + 0.16, v + 0.1, 0.93, 0.935, rnd.choice(ART), "Neon",
                      collide=False, shadow=False)
    screen_sign(R, par, 0.0, R.D - 0.3, (0, -1), min(6.0, R.W - 4), 2.2, 1.4, name, accent, style="led")
    ceiling_lights(R, par, h, 3)


def t_florist(R, par, name, accent, h):
    (l0, l1), (r0, r1), (v0, v1) = zones(R)
    flowers = [(230, 70, 90), (250, 200, 60), (240, 240, 236), (200, 90, 200), (250, 130, 60), (240, 150, 180)]
    for u0, u1, wall_u, face in ((l0, l1, -R.W / 2 + 0.5, (1, 0)), (r0, r1, R.W / 2 - 0.5, (-1, 0))):
        for v in along(v0 + 0.6, v1 - 0.4, 1.4, 10):
            q = R.p(wall_u, v)
            vcyl(par, "Bucket", q[0], q[1], R.z, 0.5, 0.5, (90, 110, 120), "Metal")
            c = rnd.choice(flowers)
            for k in range(2):
                ball(par, "Flowers", q[0] + rnd.uniform(-0.12, 0.12), q[1] + rnd.uniform(-0.12, 0.12),
                     R.z + 0.75 + rnd.uniform(0, 0.25), 0.32, c if k else (80, 130, 60), "Fabric", collide=False)
    counter(R, par, r0 + 0.3, R.D * 0.7, r1 - 1.2, R.D * 0.7 + 0.7, (230, 226, 218), (150, 104, 66))
    for u, v in grid(l0 + 0.8, l1 - 0.4, v0 + 1.5, v1 - 1.5, 2.6, 3.0, cap=6):
        R.box(par, "Flower stand", u - 0.5, v - 0.5, u + 0.5, v + 0.5, 0, 0.7, (150, 104, 66), "Wood")
        for k in range(4):
            q = R.p(u + rnd.uniform(-0.3, 0.3), v + rnd.uniform(-0.3, 0.3))
            ball(par, "Flowers", q[0], q[1], R.z + 0.85, 0.35, rnd.choice(flowers), "Fabric", collide=False)
    ceiling_lights(R, par, h)


def t_clinic(R, par, name, accent, h):
    (l0, l1), (r0, r1), (v0, v1) = zones(R)
    counter(R, par, r0 + 0.3, v0 + 1.6, r1 - 0.3, v0 + 2.3, (236, 240, 242), (120, 190, 200))
    for u in along(l0 + 0.5, l1 - 0.2, 0.7, 10):
        chair(R, par, u, v0 + 0.6, (0, 1), (90, 150, 170))
    for k, v in enumerate(along(R.D * 0.5, v1 - 1.0, 2.8, 4)):
        R.box(par, "Exam bed", l0 + 0.2, v - 0.4, l0 + 2.2, v + 0.4, 0, 0.75, (236, 240, 242), "Fabric")
        R.box(par, "Curtain", l0, v + 0.9, l1 - 0.2, v + 0.94, 0.2, 2.2, (150, 200, 210), "Fabric", tr=0.2)
    cross = R.obj(par, "Cross", 0.0, R.D - 0.3, h - 1.4, 0.9, 0.1, 0.3, (0, -1), (60, 200, 120), "Neon")
    R.obj(par, "Cross", 0.0, R.D - 0.3, h - 1.7, 0.3, 0.1, 0.9, (0, -1), (60, 200, 120), "Neon")
    plant(R, par, r1 - 0.4, v1 - 0.4, 1.2)
    ceiling_lights(R, par, h, 3)


def t_music(R, par, name, accent, h):
    (l0, l1), (r0, r1), (v0, v1) = zones(R)
    for k, v in enumerate(along(v0 + 0.6, v1 - 0.4, 0.9, 14)):
        c = rnd.choice([(200, 60, 40), (230, 200, 150), (30, 30, 34), (60, 120, 200), (240, 240, 236)])
        R.obj(par, "Guitar body", -R.W / 2 + 0.15, v, 1.0, 0.42, 0.1, 0.55, (1, 0), c, "Wood")
        R.obj(par, "Guitar neck", -R.W / 2 + 0.15, v, 1.55, 0.07, 0.06, 0.75, (1, 0), (60, 40, 30), "Wood")
    R.obj(par, "Piano", (r0 + r1) / 2, R.D * 0.35, 0, 1.6, 0.7, 1.2, (0, -1), (16, 16, 18), "SmoothPlastic", refl=0.2)
    R.obj(par, "Piano keys", (r0 + r1) / 2, R.D * 0.35 - 0.45, 0.7, 1.4, 0.25, 0.05, (0, -1), (245, 245, 240))
    q = R.p((r0 + r1) / 2, R.D * 0.35 - 0.9)
    seat(par, q[0], q[1], R.z, R.phi(0, 1), (16, 16, 18), back=False, w=0.9)
    du, dv = (r0 + r1) / 2, R.D * 0.68
    rug(R, par, du, dv, 2.6, 2.2, (120, 40, 50))
    for k, (x, y, d_, hh) in enumerate(((0, 0.3, 0.6, 0.45), (-0.7, -0.2, 0.4, 0.6), (0.7, -0.2, 0.4, 0.6),
                                        (-0.4, 0.6, 0.35, 0.75), (0.4, 0.6, 0.35, 0.75))):
        q = R.p(du + x, dv + y)
        vcyl(par, "Drum", q[0], q[1], R.z, hh, d_, (200, 40, 50) if k == 0 else (230, 230, 226), "SmoothPlastic")
    counter(R, par, r0 + 0.2, v0 + 0.6, r0 + 0.9, v0 + 2.6, (30, 30, 34), (150, 104, 66))
    ceiling_lights(R, par, h)


def t_bowling(R, par, name, accent, h):
    (l0, l1), (r0, r1), (v0, v1) = zones(R)
    lanes = [l0 + 0.7, l0 + 2.3] if l1 - l0 > 3.4 else [l0 + 0.9]
    for u in lanes:
        R.box(par, "Lane", u - 0.55, v0 + 1.0, u + 0.55, v1 - 0.3, 0, 0.04, (214, 170, 110), "WoodPlanks")
        for e in (-1, 1):
            R.box(par, "Gutter", u + e * 0.62 - 0.07, v0 + 1.0, u + e * 0.62 + 0.07, v1 - 0.3, 0, 0.02, (60, 62, 66), "Metal")
        for row in range(4):
            for k in range(row + 1):
                q = R.p(u + (k - row / 2) * 0.3, v1 - 1.6 + row * 0.26)
                pin = vcyl(par, "Pin", q[0], q[1], R.z + 0.04, 0.38, 0.12, (245, 245, 240), "SmoothPlastic")
                pin.props["Anchored"] = ("bool", False)
        q = R.p(u, v0 + 1.4)
        b = ball(par, "Bowling ball", q[0], q[1], R.z + 0.3, 0.45, rnd.choice([(60, 40, 160), (200, 40, 60), (30, 30, 34)]),
                 "SmoothPlastic")
        b.props["Anchored"] = ("bool", False)
    screen_sign(R, par, (l0 + l1) / 2, R.D - 0.3, (0, -1), l1 - l0 - 0.3, 1.0, h - 1.4, "STRIKE!", accent)
    for u, v in grid(r0 + 0.5, r1 - 0.3, v0 + 0.6, R.D * 0.55, 2.6, 2.6, cap=6):
        table(R, par, u, v, 0.8, 0.8, (30, 30, 34))
        stool(R, par, u - 0.6, v, accent)
        stool(R, par, u + 0.6, v, accent)
    counter(R, par, r1 - 0.8, R.D * 0.62, r1, v1 - 0.4, (30, 30, 34), (200, 60, 50))
    neon_strip(R, par, -R.W / 2 + 0.2, 0.3, -R.W / 2 + 0.24, R.D - 0.3, h - 0.3, accent)
    ceiling_lights(R, par, h, 3)


def t_market(R, par, name, accent, h):
    (l0, l1), (r0, r1), (v0, v1) = zones(R)
    goods = [(230, 70, 60), (250, 200, 60), (70, 160, 90), (60, 120, 210), (240, 140, 50), (200, 200, 196)]
    for u in along(l0 + 0.7, l1 - 0.4, 2.2, 5):
        R.box(par, "Aisle", u - 0.45, v0 + 1.4, u + 0.45, v1 - 1.2, 0, 1.7, (236, 236, 232), "Metal")
        for e in (-1, 1):
            for z in (0.3, 0.75, 1.2):
                R.box(par, "Goods", u + e * 0.45 - 0.04, v0 + 1.5, u + e * 0.47, v1 - 1.3, z, z + 0.3, rnd.choice(goods),
                      collide=False)
    R.box(par, "Fridges", R.W / 2 - 0.9, v0 + 2.6, R.W / 2 - 0.2, v1 - 0.3, 0, 2.1, (230, 232, 234), "Metal")
    R.box(par, "Fridge glass", R.W / 2 - 0.92, v0 + 2.7, R.W / 2 - 0.9, v1 - 0.4, 0.2, 1.95, (170, 230, 255), "Neon",
          tr=0.4, collide=False, shadow=False)
    for u in (r0 + 0.5, r0 + 2.3):
        if u < r1 - 1.2:
            counter(R, par, u, v0 + 0.9, u + 0.6, v0 + 2.2, (60, 62, 66), (230, 228, 222))
    screen_sign(R, par, 0.0, R.D - 0.3, (0, -1), 3.4, 0.8, h - 1.1, name + "  ·  OPEN 24/7", accent, style="led")
    ceiling_lights(R, par, h, 3)


def t_cowork(R, par, name, accent, h):
    (l0, l1), (r0, r1), (v0, v1) = zones(R)
    for u, v in grid(l0, l1, v0 + 0.8, v1 - 0.6, 2.2, 2.4, cap=12):
        desk(R, par, u, v, (0, 1), 1.3, screen=accent)
    for k, (u, v) in enumerate(grid(r0 + 0.3, r1 - 0.3, R.D * 0.55, v1 - 0.4, 1.8, 1.8, cap=6)):
        q = R.p(u, v)
        ball(par, "Bean bag", q[0], q[1], R.z + 0.25, 0.9, rnd.choice(ART), "Fabric")
    R.box(par, "Whiteboard", R.W / 2 - 0.08, v0 + 0.8, R.W / 2 - 0.04, R.D * 0.45, 0.9, 2.1, (250, 250, 250))
    table(R, par, (r0 + r1) / 2, R.D * 0.28, 2.0, 1.0, (240, 240, 236))
    for e in (-1, 1):
        chair(R, par, (r0 + r1) / 2 + e * 0.5, R.D * 0.28 - 0.9, (0, 1), (40, 44, 52))
        chair(R, par, (r0 + r1) / 2 + e * 0.5, R.D * 0.28 + 0.9, (0, -1), (40, 44, 52))
    plant(R, par, l0 + 0.4, v0, 1.5)
    ceiling_lights(R, par, h, 3)


def t_arcade(R, par, name, accent, h):
    (l0, l1), (r0, r1), (v0, v1) = zones(R)
    for wall_u, face in ((-R.W / 2 + 0.5, (1, 0)), (R.W / 2 - 0.5, (-1, 0))):
        for v in along(v0 + 0.8, v1 - 0.5, 1.4, 12):
            c = rnd.choice(ART)
            R.obj(par, "Arcade cabinet", wall_u, v, 0, 0.8, 0.8, 1.8, face, (24, 24, 30))
            su, sv = R.at(wall_u, v, face, 0.3)
            R.obj(par, "Arcade screen", su, sv, 1.0, 0.6, 0.22, 0.45, face, c, "Neon", shadow=False)
            R.obj(par, "Marquee", su, sv, 1.6, 0.7, 0.2, 0.18, face, accent, "Neon", shadow=False)
    R.box(par, "Air hockey", (l0 + l1) / 2 + 0.2 - 0.7, R.D * 0.45 - 1.1, (l0 + l1) / 2 + 0.2 + 0.7, R.D * 0.45 + 1.1, 0,
          0.8, (230, 230, 236))
    R.box(par, "Air hockey glow", (l0 + l1) / 2 + 0.2 - 0.65, R.D * 0.45 - 1.05, (l0 + l1) / 2 + 0.2 + 0.65,
          R.D * 0.45 + 1.05, 0.8, 0.82, (60, 200, 255), "Neon", collide=False)
    cu, cv = (r0 + r1) / 2 - 0.3, R.D * 0.45
    R.box(par, "Claw machine", cu - 0.5, cv - 0.5, cu + 0.5, cv + 0.5, 0, 0.9, accent)
    R.box(par, "Claw glass", cu - 0.5, cv - 0.5, cu + 0.5, cv + 0.5, 0.9, 1.9, (200, 230, 240), "Glass", tr=0.6)
    for k in range(5):
        q = R.p(cu + rnd.uniform(-0.3, 0.3), cv + rnd.uniform(-0.3, 0.3))
        ball(par, "Prize", q[0], q[1], R.z + 1.05, 0.25, rnd.choice(ART), "Fabric", collide=False)
    for u in along(-R.W / 2 + 1, R.W / 2 - 1, 3.5, 6):
        lamp_panel(R, par, u, R.D / 2, h, w=0.4, d=R.D * 0.8, rng=14, brightness=0.6, color=(200, 120, 255),
                   lit=abs(u) < 1.5)


def t_pets(R, par, name, accent, h):
    (l0, l1), (r0, r1), (v0, v1) = zones(R)
    for v in along(v0 + 1.0, v1 - 0.6, 2.2, 8):
        R.box(par, "Aquarium stand", -R.W / 2 + 0.2, v - 0.6, -R.W / 2 + 0.8, v + 0.6, 0, 0.8, (40, 42, 46), "Wood")
        R.box(par, "Aquarium", -R.W / 2 + 0.2, v - 0.6, -R.W / 2 + 0.8, v + 0.6, 0.8, 1.6, (60, 170, 230), "Neon",
              tr=0.55, shadow=False)
        for k in range(2):
            q = R.p(-R.W / 2 + 0.5, v + rnd.uniform(-0.4, 0.4))
            ball(par, "Fish", q[0], q[1], R.z + rnd.uniform(1.0, 1.4), 0.14, rnd.choice([(250, 140, 40), (250, 220, 60)]),
                 "Neon", collide=False)
    for u, v in grid(r0 + 0.3, r1 - 0.3, v0 + 0.8, v1 - 0.6, 2.2, 2.4, cap=8):
        q = R.p(u, v)
        vcyl(par, "Pet bed", q[0], q[1], R.z, 0.2, 0.9, rnd.choice(ART), "Fabric")
    shelf(R, par, l1 - 0.3, R.D * 0.5, (-1, 0), w=2.0, h=1.6, color=(236, 236, 232),
          stock=[(200, 80, 60), (90, 160, 90), (240, 200, 70)], rows=3)
    counter(R, par, l0 + 1.4, v0 + 0.8, l1 - 0.6, v0 + 1.5, (90, 150, 110), (230, 226, 218))
    ceiling_lights(R, par, h)


def t_salon(R, par, name, accent, h):
    (l0, l1), (r0, r1), (v0, v1) = zones(R)
    for v in along(v0 + 0.9, v1 - 0.5, 1.8, 8):
        R.box(par, "Mirror", -R.W / 2 + 0.08, v - 0.5, -R.W / 2 + 0.12, v + 0.5, 0.9, 2.1, (210, 220, 226), "Glass",
              refl=0.6)
        R.box(par, "Vanity", -R.W / 2 + 0.12, v - 0.6, -R.W / 2 + 0.5, v + 0.6, 0, 0.85, (236, 236, 232), "Marble")
        q = R.p(-R.W / 2 + 1.2, v)
        seat(par, q[0], q[1], R.z + 0.1, R.phi(-1, 0), (30, 30, 34), back=True, w=0.6)
    sofa(R, par, (r0 + r1) / 2, v0 + 1.0, (0, 1), w=2.0, color=accent)
    counter(R, par, r1 - 0.7, R.D * 0.5, r1, v1 - 0.6, (236, 236, 232), (30, 30, 34))
    plant(R, par, r1 - 0.4, v0 + 0.4, 1.3)
    ceiling_lights(R, par, h)


def t_pizza(R, par, name, accent, h):
    t_cafe(R, par, name, accent, h, menu="MARGHERITA · PANEER TIKKA · FUNGHI · GARLIC KNOTS")
    (l0, l1), (r0, r1), (v0, v1) = zones(R)
    q = R.p(R.W / 2 - 1.0, R.D - 1.2)
    ball(par, "Pizza oven", q[0], q[1], R.z + 0.9, 1.8, (170, 90, 60), "Brick")
    R.box(par, "Oven fire", R.W / 2 - 1.6, R.D - 1.6, R.W / 2 - 1.4, R.D - 0.9, 0.9, 1.2, (255, 120, 30), "Neon",
          collide=False, shadow=False)


def t_icecream(R, par, name, accent, h):
    t_cafe(R, par, name, accent, h, menu="MANGO · PISTACHIO · CHOCOLATE · FILTER COFFEE · STRAWBERRY")
    (l0, l1), (r0, r1), (v0, v1) = zones(R)
    for k, c in enumerate(((250, 200, 90), (150, 210, 130), (120, 80, 60), (250, 170, 190), (240, 236, 220))):
        R.box(par, "Ice cream tub", r1 - 1.1, v1 * 0.4 + k * 0.4, r1 - 0.8, v1 * 0.4 + k * 0.4 + 0.3, 0.96, 1.0, c, "Neon",
              collide=False, shadow=False)


BUSINESS = [   # name, theme, accent
    ("BREW & BLOOM CAFÉ", t_cafe, (230, 140, 80)), ("GLASS CITY BANK", t_bank, (60, 120, 210)),
    ("PULSE GYM", t_gym, (240, 60, 80)), ("ATELIER NINE GALLERY", t_gallery, (240, 236, 228)),
    ("PAPER MOON BOOKS", t_books, (90, 150, 230)), ("SAFFRON KITCHEN", t_restaurant, (240, 170, 40)),
    ("BYTE LABS STORE", t_tech, (60, 200, 255)), ("PETAL POST FLORIST", t_florist, (235, 120, 170)),
    ("CITY CARE CLINIC", t_clinic, (60, 200, 120)), ("STUDIO NINE MUSIC", t_music, (200, 60, 60)),
    ("STRIKE LANES BOWLING", t_bowling, (255, 90, 200)), ("FRESHMART", t_market, (90, 200, 90)),
    ("CO-LAB WORKSPACE", t_cowork, (250, 180, 60)), ("PIXEL ARCADE", t_arcade, (160, 90, 255)),
    ("PAWS & FINS", t_pets, (60, 170, 230)), ("SHEAR GENIUS SALON", t_salon, (200, 120, 220)),
    ("SLICE OF NAPOLI", t_pizza, (220, 60, 50)), ("SCOOP DREAMS", t_icecream, (250, 160, 190)),
]


# ---- an open-plan office floor, a penthouse and a building lobby: rooms reached by lift
def t_office(R, par, name, accent, h):
    (l0, l1), (r0, r1), (v0, v1) = zones(R)
    for u, v in grid(l0, l1, v0 + 0.6, v1 - 0.5, 2.2, 2.6, cap=12):
        desk(R, par, u, v, (0, 1), 1.3, screen=accent)
    mu0, mu1, mv0, mv1 = r0 + 0.2, r1, v0 + 0.2, min(v0 + 4.4, v1 * 0.55)
    for a_, b_ in (((mu0, mv1), (mu1, mv1)), ((mu0, mv0), (mu0, mv1 - 1.0))):
        R.box(par, "Meeting room glass", min(a_[0], b_[0]) - 0.03, min(a_[1], b_[1]) - 0.03, max(a_[0], b_[0]) + 0.03,
              max(a_[1], b_[1]) + 0.03, 0, h - 0.05, (190, 220, 230), "Glass", tr=0.6, shadow=False)
    table(R, par, (mu0 + mu1) / 2 + 0.2, (mv0 + mv1) / 2, max(1.2, mu1 - mu0 - 1.8), 1.0, (240, 240, 236))
    for e in (-1, 1):
        chair(R, par, (mu0 + mu1) / 2 + 0.2 + e * 0.5, (mv0 + mv1) / 2 - 0.9, (0, 1), (40, 44, 52))
        chair(R, par, (mu0 + mu1) / 2 + 0.2 + e * 0.5, (mv0 + mv1) / 2 + 0.9, (0, -1), (40, 44, 52))
    screen_sign(R, par, R.W / 2 - 0.1, (mv0 + mv1) / 2, (-1, 0), 1.6, 0.9, 1.1, name + "\nQ4 PLAN", accent)
    kitchen_run(R, par, r0 + 0.4, r1 - 0.2, R.D - 0.15, -1)
    for v in (R.D * 0.68,):
        sofa(R, par, (r0 + r1) / 2, v, (0, -1), w=2.0, color=accent)
    plant(R, par, l0 + 0.3, v1, 1.6)
    plant(R, par, r0 + 0.3, mv1 + 0.6, 1.2)
    ceiling_lights(R, par, h, 3)


def t_penthouse(R, par, name, accent, h):
    (l0, l1), (r0, r1), (v0, v1) = zones(R)
    lu = (l0 + l1) / 2
    rug(R, par, lu, R.D * 0.32, l1 - l0 - 0.6, 3.0, accent)
    sofa(R, par, lu, R.D * 0.32 + 1.0, (0, -1), w=min(2.6, l1 - l0 - 0.6), color=(220, 214, 204))
    table(R, par, lu, R.D * 0.32, 1.1, 0.6, (150, 104, 66), h=0.4)
    tv(R, par, lu, v0 + 0.25, (0, 1), 1.6)
    floor_lamp(R, par, l0 + 0.3, R.D * 0.32 + 1.2)
    dining(R, par, lu, R.D * 0.7, 1.6, 0.9, 4)
    pendant(R, par, lu, R.D * 0.7, h, 1.0, lit=True)
    bu = (r0 + r1) / 2
    bed(R, par, bu, v0 + 1.25, (0, 1), w=1.8, L=2.1, color=accent)
    R.obj(par, "Nightstand", bu - 1.25, v0 + 0.3, 0, 0.5, 0.4, 0.55, (0, 1), (150, 104, 66), "Wood")
    R.obj(par, "Nightstand", bu + 1.25, v0 + 0.3, 0, 0.5, 0.4, 0.55, (0, 1), (150, 104, 66), "Wood")
    R.obj(par, "Wardrobe", r1 - 0.35, R.D * 0.48, 0, 1.8, 0.6, 2.2, (-1, 0), (236, 232, 224), "Wood")
    kitchen_run(R, par, r0 + 0.2, r1 - 0.2, R.D - 0.15, -1)
    counter(R, par, r0 + 0.8, R.D * 0.68, r1 - 0.8, R.D * 0.68 + 0.8, (60, 62, 66), (236, 236, 232))
    for u in np.arange(r0 + 1.1, r1 - 0.8, 0.7):
        stool(R, par, u, R.D * 0.68 - 0.4, accent)
    R.box(par, "Bath", r1 - 1.8, R.D * 0.25, r1 - 0.2, R.D * 0.25 + 0.8, 0, 0.55, (245, 245, 242), "Marble")
    R.box(par, "Bath water", r1 - 1.7, R.D * 0.25 + 0.1, r1 - 0.3, R.D * 0.25 + 0.7, 0.4, 0.5, (90, 180, 220), "Glass",
          tr=0.3, collide=False)
    plant(R, par, l0 + 0.3, v1, 1.5)
    painting(R, par, -R.W / 2 + 0.1, R.D * 0.55, (1, 0), 1.6, 1.0, 1.2)
    ceiling_lights(R, par, h, 2)


def t_lobby(R, par, name, accent, h, mailboxes=False):
    (l0, l1), (r0, r1), (v0, v1) = zones(R)
    counter(R, par, r0 + 0.4, R.D * 0.55, r1 - 0.6, R.D * 0.55 + 0.75, (40, 40, 44), (230, 228, 222), h=1.05)
    sofa(R, par, (l0 + l1) / 2, R.D * 0.35, (1, 0), w=2.0, color=accent)
    table(R, par, (l0 + l1) / 2 + 1.2, R.D * 0.35, 0.8, 1.2, (150, 104, 66), h=0.4)
    if mailboxes:
        R.box(par, "Mailboxes", -R.W / 2 + 0.1, R.D * 0.55, -R.W / 2 + 0.45, R.D * 0.55 + 2.4, 0.6, 2.0,
              (180, 160, 120), "Metal")
    name_board(R, par, 0.0, R.D - 0.3, (0, -1), min(5.0, R.W - 5), h - 1.0, name, (24, 26, 30))
    plant(R, par, l0 + 0.4, v0, 1.6)
    plant(R, par, r1 - 0.4, v0, 1.6)
    painting(R, par, R.W / 2 - 0.1, R.D * 0.3, (-1, 0), 2.0, 1.2, 1.2)
    ceiling_lights(R, par, h, 2)


# ---- tower lobbies: double height, marble, an LED wall with the tower's name
def t_grand_lobby(R, par, name, accent, h, variant=0):
    (l0, l1), (r0, r1), (v0, v1) = zones(R)
    cu = (r0 + r1) / 2
    counter(R, par, cu - 2.6, R.D * 0.5, cu + 2.6, R.D * 0.5 + 0.9, (230, 228, 222), (40, 38, 36), h=1.1)
    neon_strip(R, par, cu - 2.6, R.D * 0.5 - 0.04, cu + 2.6, R.D * 0.5, 0.15, accent)
    screen_sign(R, par, R.W / 2 - 0.15, R.D * 0.5, (-1, 0), min(7.0, R.D * 0.6), 3.6, 2.2, name, accent, style="led")
    for u in (l0 + 1.2, r1 - 1.2):
        sculpture(R, par, u, v0 + 1.8, plinth(R, par, u, v0 + 1.8, 0.9, 1.1))
    for e, wall_u in ((1, -R.W / 2 + 0.5), (-1, R.W / 2 - 0.5)):
        for v in (R.D * 0.22, R.D * 0.78):
            R.obj(par, "Bench", wall_u, v, 0, 2.4, 0.6, 0.45, (e, 0), (40, 38, 36), "Marble")
    if variant == 1:                     # a car showroom: two cars on turntables
        for k, v in enumerate((R.D * 0.32, R.D * 0.72)):
            u = (l0 + l1) / 2
            q = R.p(u, v)
            m = new(par, "Model", "Spin")
            vcyl(m, "Turntable", q[0], q[1], R.z, 0.12, 4.2, (60, 62, 66), "Metal", refl=0.2)
            c = rnd.choice([(200, 30, 40), (240, 240, 236), (30, 60, 140), (20, 20, 22), (250, 180, 30)])
            ybox(m, "Car body", q[0], q[1], R.z + 0.42, 1.9, 4.4, 0.6, k * 0.8, c, "SmoothPlastic", refl=0.3)
            ybox(m, "Car cabin", q[0], q[1], R.z + 1.02, 1.7, 2.2, 0.5, k * 0.8, (30, 36, 44), "Glass", refl=0.3)
            X, Z = np.array([math.cos(k * 0.8), math.sin(k * 0.8)]), np.array([math.sin(k * 0.8), -math.cos(k * 0.8)])
            for wx in (-0.9, 0.9):
                for wz in (-1.35, 1.35):
                    w_ = q + X * wx + Z * wz
                    mbox(m, "Wheel", (w_[0], w_[1], R.z + 0.47), ((X[0], X[1], 0), (0, 0, 1), (Z[0], Z[1], 0)),
                         (0.26, 0.7, 0.7), (26, 26, 28), shape=2)
            light(m.kids[0], rng=14, brightness=0.8)
    elif variant == 2:                   # an atrium garden
        for v in (R.D * 0.3, R.D * 0.7):
            u = (l0 + l1) / 2
            R.box(par, "Planter", u - 1.6, v - 1.6, u + 1.6, v + 1.6, 0, 0.6, (230, 228, 222), "Marble")
            tree(par, R.p(u, v), 6.0, 2.4, SPECIES[rnd.choice([0, 1, 3])], n=5, z0=R.z + 0.5)
    else:                                # lounge: sofas and a sculpture
        for v in (R.D * 0.3, R.D * 0.7):
            u = (l0 + l1) / 2
            rug(R, par, u, v, 3.6, 3.0, (60, 60, 64))
            sofa(R, par, u - 0.9, v, (1, 0), w=2.2, color=accent)
            sofa(R, par, u + 1.1, v, (-1, 0), w=2.2, color=(220, 214, 204))
            table(R, par, u + 0.1, v, 0.7, 1.2, (40, 38, 36), h=0.4, mat="Marble")
    q = R.p(0.0, R.D * 0.3)
    vcyl(par, "Chandelier", q[0], q[1], R.z + h - 1.6, 0.08, 3.2, (255, 230, 180), "Neon", collide=False, shadow=False)
    vcyl(par, "Chandelier", q[0], q[1], R.z + h - 1.2, 0.08, 2.2, (255, 230, 180), "Neon", collide=False, shadow=False)
    light(par.kids[-1], rng=26, brightness=1.0, color=(255, 226, 180))
    vcyl(par, "Chandelier rod", q[0], q[1], R.z + h - 1.6, 1.6, 0.05, (200, 190, 150), "Metal", collide=False)
    for u in (l0 + 0.5, r1 - 0.5):
        for v in (v0 + 0.2, v1 - 0.3):
            plant(R, par, u, v, 2.0, (40, 40, 44))
    lamp_panel(R, par, 0.0, R.D * 0.7, h, w=2.0, d=2.0, rng=26, brightness=0.9)



# ---- sky lounges: the glass room at the top of a tower, round its central lift core (|u|, and v
# about D/2, within CORE of the middle). Things stand round the windows and behind the core.
def lounge_spots(R, core, gap=1.2):
    """Places round a lounge, clear of its core and of the walk out of the lift (in front of it)."""
    out = []
    for u, v in grid(-R.W / 2 + 1.2, R.W / 2 - 1.2, 1.2, R.D - 1.2, 3.2, 3.2):
        if abs(u) < core + gap and abs(v - R.D / 2) < core + gap:
            continue
        if abs(u) < 2.0 and v < R.D / 2:
            continue
        out.append((u, v))
    return out


def window_spots(R, step=3.4, m=1.4):
    """Points just inside each glass wall, facing out: (u, v, face)."""
    out = []
    for u in np.arange(-R.W / 2 + m, R.W / 2 - m + 1e-6, step):
        out += [(u, 0.9, (0, -1)), (u, R.D - 0.9, (0, 1))]
    for v in np.arange(m + 1.5, R.D - m - 1.5 + 1e-6, step):
        out += [(-R.W / 2 + 0.9, v, (-1, 0)), (R.W / 2 - 0.9, v, (1, 0))]
    return out


def l_bar(R, par, name, accent, h, core):
    vb = R.D / 2 + core + 1.6
    counter(R, par, -core - 1.0, vb, core + 1.0, vb + 0.7, (24, 24, 28), (230, 228, 222), h=1.1)
    neon_strip(R, par, -core - 1.0, vb - 0.03, core + 1.0, vb, 0.1, accent)
    for u in np.arange(-core - 0.6, core + 0.8, 0.75):
        stool(R, par, u, vb - 0.45, accent)
    R.box(par, "Back bar", -core - 1.0, R.D - 0.6, core + 1.0, R.D - 0.25, 1.1, 2.6, (40, 30, 26), "Wood")
    R.box(par, "Back bar glow", -core - 0.9, R.D - 0.62, core + 0.9, R.D - 0.6, 1.3, 2.4, accent, "Neon", collide=False)
    for u, v, face in thin(window_spots(R, 4.4), 14):
        if abs(u) < core + 2 and v > R.D / 2:
            continue
        su, sv = R.at(u, v, face, -0.2)
        sofa(R, par, su, sv, (-face[0], -face[1]), w=1.8, color=rnd.choice([(60, 60, 66), accent, (220, 214, 204)]))
    for u, v in thin(lounge_spots(R, core, 2.0), 8):
        table(R, par, u, v, 0.7, 0.7, (40, 38, 36), h=0.45, mat="Marble")


def l_observatory(R, par, name, accent, h, core):
    for u, v, face in thin(window_spots(R, 4.0), 12):
        q = R.p(*R.at(u, v, face, -0.2))
        for k in range(3):
            ang = k * 2.1
            vcyl(par, "Tripod leg", q[0] + 0.25 * math.cos(ang), q[1] + 0.25 * math.sin(ang), R.z, 1.1, 0.05,
                 (40, 40, 44), "Metal")
        g = R.a * face[0] - R.f * face[1]
        X = np.array([g[0], g[1], 0.6])
        X /= np.linalg.norm(X)
        Z = np.array([-g[1], g[0], 0.0])
        Y = np.cross(Z, X)
        mbox(par, "Telescope", (q[0], q[1], R.z + 1.35), (tuple(X), tuple(Y), tuple(Z)), (1.0, 0.22, 0.22),
             (230, 230, 226), "Metal", shape=2)
    screen_sign(R, par, 0.0, R.D - 0.3, (0, -1), min(8.0, R.W - 6), 2.4, 1.2, "STAR MAP\n" + name, accent)
    for u, v in thin(lounge_spots(R, core, 2.5), 5):
        R.obj(par, "Bench", u, v, 0, 1.6, 0.5, 0.45, (0, 1), (40, 40, 44), "Wood")


def l_garden(R, par, name, accent, h, core):
    for u, v in thin(lounge_spots(R, core, 1.5), 14):
        if rnd.random() < 0.55:
            R.box(par, "Planter", u - 1.1, v - 1.1, u + 1.1, v + 1.1, 0, 0.55, (226, 222, 214), "Marble")
            R.box(par, "Lawn", u - 1.0, v - 1.0, u + 1.0, v + 1.0, 0.55, 0.6, GRASS, "Grass")
            tree(par, R.p(u, v), min(h - 1.0, 4.6), 1.6, SPECIES[rnd.choice([0, 1, 2, 3])], n=4, z0=R.z + 0.55)
        elif rnd.random() < 0.5:
            R.obj(par, "Bench", u, v, 0, 1.6, 0.5, 0.45, (0, 1), (150, 104, 66), "Wood")
    R.box(par, "Reflecting pool", -core - 0.5, R.D / 2 + core + 1.2, core + 0.5, R.D / 2 + core + 3.0, 0, 0.12,
          (70, 160, 200), "Glass", tr=0.25, refl=0.3, collide=False)


def l_club(R, par, name, accent, h, core):
    cols = [(255, 60, 160), (60, 200, 255), (255, 200, 40), (140, 80, 255), (60, 255, 140)]
    for e in (-1, 1):
        u0, u1 = sorted((e * (core + 1.5), e * (R.W / 2 - 1.2)))
        for u in along(u0, u1 - 1.5, 1.6, 5):
            for v in along(1.2, R.D - 2.4, 1.6, 9):
                R.box(par, "DanceTile", u, v, u + 1.55, v + 1.55, 0, 0.04, rnd.choice(cols), "Neon", shadow=False)
    vb = R.D / 2 + core + 1.2
    R.box(par, "DJ booth", -1.6, vb, 1.6, vb + 0.9, 0, 1.1, (20, 20, 24), "Metal")
    neon_strip(R, par, -1.6, vb - 0.03, 1.6, vb, 0.5, accent, h=0.3)
    for e in (-1, 1):
        R.box(par, "Speaker", e * 2.4 - 0.4, vb, e * 2.4 + 0.4, vb + 0.7, 0, 2.0, (16, 16, 18))
    screen_sign(R, par, 0.0, R.D - 0.3, (0, -1), min(8.0, R.W - 4), 2.6, 1.4, name, accent, style="led")
    for side_u in (-R.W / 2 + 0.3, R.W / 2 - 0.3):
        R.box(par, "Neon strip", side_u - 0.03, 0.5, side_u + 0.03, R.D - 0.5, h - 0.4, h - 0.32, accent, "Neon",
              collide=False)


def l_dining(R, par, name, accent, h, core):
    for u, v, face in thin(window_spots(R, 3.6), 12):
        if abs(u) < core + 2 and v > R.D / 2:
            continue
        tu, tv_ = R.at(u, v, face, -0.7)
        table(R, par, tu, tv_, 0.9, 0.9, (246, 244, 238), mat="Fabric")
        for s in (-1, 1):
            cu, cv = R.at(tu, tv_, face, 0.0, s * 0.75)
            chair(R, par, cu, cv, ((tu - cu) / 0.75, (tv_ - cv) / 0.75), (110, 40, 40))
        q = R.p(tu, tv_)
        ball(par, "Candle", q[0], q[1], R.z + 0.82, 0.1, (255, 190, 90), "Neon", collide=False, shadow=False)
    vb = R.D / 2 + core + 1.8
    R.obj(par, "Grand piano", 0.0, vb, 0, 1.5, 2.0, 1.0, (0, -1), (16, 16, 18), refl=0.25)
    q = R.p(0.0, vb - 1.3)
    seat(par, q[0], q[1], R.z, R.phi(0, 1), (16, 16, 18), back=False, w=0.9)


def l_pool(R, par, name, accent, h, core):
    v0 = R.D / 2 + core + 1.0
    R.box(par, "Pool edge", -R.W / 2 + 0.8, v0, R.W / 2 - 0.8, R.D - 0.8, 0, 0.45, (236, 236, 232), "Marble")
    R.box(par, "Pool", -R.W / 2 + 1.1, v0 + 0.3, R.W / 2 - 1.1, R.D - 1.1, 0.25, 0.42, (40, 170, 220), "Glass",
          tr=0.25, refl=0.3, collide=False)
    neon_strip(R, par, -R.W / 2 + 1.1, v0 + 0.28, R.W / 2 - 1.1, v0 + 0.3, 0.3, (120, 230, 255))
    for u in along(-R.W / 2 + 1.6, R.W / 2 - 1.2, 1.6, 10):
        if abs(u) < 2.2:
            continue
        R.obj(par, "Lounger", u, 2.0, 0, 0.7, 1.9, 0.35, (0, 1), (240, 240, 236), "Fabric")
    for e in (-1, 1):
        plant(R, par, e * (R.W / 2 - 1.0), 1.0, 1.8)
        q = R.p(e * (R.W / 2 - 2.6), 3.6)
        vcyl(par, "Umbrella pole", q[0], q[1], R.z, 2.4, 0.08, (230, 230, 226), "Metal")
        vcyl(par, "Umbrella", q[0], q[1], R.z + 2.3, 0.2, 2.6, accent, "Fabric", collide=False)
    vb = R.D / 2 - core - 1.0
    counter(R, par, core + 2.2, vb - 2.2, core + 3.0, vb, (240, 240, 236), (40, 38, 36), h=1.1)
    for v in along(vb - 2.0, vb, 0.7, 3):
        stool(R, par, core + 1.75, v, accent)


def l_cinema(R, par, name, accent, h, core):
    screen_sign(R, par, -R.W / 2 + 0.3, R.D / 2, (1, 0), min(R.D - 3, 9), min(h - 1.5, 4.2), 0.8, "NOW SHOWING\n" + name,
                accent)
    for k, u in enumerate(along(-R.W / 2 + 4.0, R.W / 2 - 1.0, 1.6, 6)):
        if abs(u) < core + 1.2:
            continue
        for v in along(1.2, R.D - 1.0, 0.9, 10):
            if abs(v - R.D / 2) < core + 1.2 and abs(u) < core + 3:
                continue
            chair(R, par, u, v, (-1, 0), (150, 30, 40))


SKY_LOUNGES = [("Sky Bar", l_bar), ("Observatory", l_observatory), ("Sky Garden", l_garden), ("Sky Club", l_club),
               ("Sky Dining", l_dining), ("Infinity Pool", l_pool), ("Sky Cinema", l_cinema)]


# ---- rooftops you reach by lift: R is the whole roof, the lift penthouse in the middle of the back
def balustrade(R, par):
    for side in SIDES:
        side_box(R, par, "Balustrade", side, *((-R.W / 2, R.W / 2) if side in ("front", "back") else (0.06, R.D - 0.06)),
                 0.0, 1.1, 0.06, **GLAZING)
        side_box(R, par, "Handrail", side, *((-R.W / 2, R.W / 2) if side in ("front", "back") else (0.06, R.D - 0.06)),
                 1.1, 1.16, 0.08, MULL, "Metal")


def r_garden(R, par, accent):
    for u, v in grid(-R.W / 2 + 1.5, R.W / 2 - 1.5, 1.5, R.D - 4.5, 5.0, 5.0, cap=10):
        if abs(u) < 2.0:
            R.obj(par, "Bench", u, v, 0, 1.6, 0.5, 0.45, (0, 1), (150, 104, 66), "Wood")
            continue
        R.box(par, "Planter", u - 1.2, v - 1.2, u + 1.2, v + 1.2, 0, 0.6, (226, 222, 214), "Concrete")
        R.box(par, "Lawn", u - 1.1, v - 1.1, u + 1.1, v + 1.1, 0.6, 0.65, GRASS, "Grass")
        tree(par, R.p(u, v), 4.5, 1.7, SPECIES[rnd.choice([0, 1, 2, 3])], n=4, z0=R.z + 0.6)


def r_helipad(R, par, accent):
    u, v = 0.0, R.D * 0.42
    d_ = min(R.W, R.D) * 0.62
    q = R.p(u, v)
    vcyl(par, "Helipad", q[0], q[1], R.z, 0.08, d_, (60, 62, 66), "Concrete")
    vcyl(par, "Helipad ring", q[0], q[1], R.z + 0.08, 0.01, d_ * 0.8, (250, 200, 40), "SmoothPlastic", collide=False)
    vcyl(par, "Helipad ring", q[0], q[1], R.z + 0.09, 0.01, d_ * 0.74, (60, 62, 66), "Concrete", collide=False)
    for e in (-1, 1):
        R.box(par, "H", u + e * 1.1 - 0.2, v - 1.6, u + e * 1.1 + 0.2, v + 1.6, 0.08, 0.1, WHITE, collide=False)
    R.box(par, "H", u - 1.1, v - 0.2, u + 1.1, v + 0.2, 0.08, 0.1, WHITE, collide=False)
    for k in range(8):
        ang = k * math.pi / 4
        p_ = q + (d_ / 2 + 0.2) * np.array([math.cos(ang), math.sin(ang)])
        ball(par, "Pad light", p_[0], p_[1], R.z + 0.12, 0.25, (60, 220, 120), "Neon", collide=False, shadow=False)
    q = R.p(R.W / 2 - 1.0, 1.0)
    vcyl(par, "Windsock pole", q[0], q[1], R.z, 3.0, 0.08, (200, 200, 196), "Metal")
    vcyl(par, "Windsock", q[0], q[1] + 0.5, R.z + 2.6, 0.4, 0.3, (250, 120, 30), "Fabric", collide=False)


def r_court(R, par, accent):
    w, d = min(R.W - 2.0, 9.0), min(R.D - 6.0, 13.0)
    R.box(par, "Court", -w / 2, 1.0, w / 2, 1.0 + d, 0, 0.04, (60, 110, 160), "SmoothPlastic")
    for (a0, b0, a1, b1) in ((-w / 2, 1.0, w / 2, 1.08), (-w / 2, 1.0 + d - 0.08, w / 2, 1.0 + d),
                             (-w / 2, 1.0, -w / 2 + 0.08, 1.0 + d), (w / 2 - 0.08, 1.0, w / 2, 1.0 + d),
                             (-w / 2, 1.0 + d / 2 - 0.04, w / 2, 1.0 + d / 2 + 0.04)):
        R.box(par, "Court line", a0, b0, a1, b1, 0.04, 0.05, WHITE, collide=False)
    R.box(par, "Hoop post", -0.1, 0.3, 0.1, 0.5, 0, 3.0, (60, 62, 66), "Metal")
    R.box(par, "Backboard", -0.9, 0.5, 0.9, 0.56, 2.9, 3.95, WHITE, "Glass", tr=0.3)
    q = R.p(0.0, 0.85)
    vcyl(par, "Hoop", q[0], q[1], R.z + 3.05, 0.04, 0.46, (240, 90, 30), "Metal", collide=False)
    q = R.p(0.8, 3.0)
    b = ball(par, "Basketball", q[0], q[1], R.z + 0.2, 0.24, (230, 110, 40), "SmoothPlastic")
    b.props["Anchored"] = ("bool", False)
    for side in ("left", "right"):
        side_box(R, par, "Fence", side, 0.06, R.D - 0.06, 1.16, 3.2, 0.04, (90, 94, 100), "DiamondPlate", tr=0.6)


def r_pool(R, par, accent):
    w, d = min(R.W - 3.0, 5.0), min(R.D - 7.0, 9.0)
    R.box(par, "Pool edge", -w / 2 - 0.4, 1.0, w / 2 + 0.4, 1.8 + d, 0, 0.45, (236, 236, 232), "Marble")
    R.box(par, "Pool", -w / 2, 1.4, w / 2, 1.4 + d, 0.25, 0.42, (40, 170, 220), "Glass", tr=0.25, refl=0.3,
          collide=False)
    for e in (-1, 1):
        for v in along(1.6, 1.4 + d, 2.2, 4):
            u = e * (w / 2 + 1.4)
            if abs(u) < R.W / 2 - 0.6:
                R.obj(par, "Lounger", u, v, 0, 0.7, 1.9, 0.35, (0, 1), (240, 240, 236), "Fabric")
    q = R.p(R.W / 2 - 1.2, R.D - 3.5)
    vcyl(par, "Umbrella pole", q[0], q[1], R.z, 2.4, 0.08, (230, 230, 226), "Metal")
    vcyl(par, "Umbrella", q[0], q[1], R.z + 2.3, 0.2, 2.6, accent, "Fabric", collide=False)


def r_bar(R, par, accent):
    counter(R, par, -R.W / 2 + 1.0, 1.0, -R.W / 2 + 1.8, min(R.D - 4.5, 7.0), (40, 30, 26), (230, 228, 222), h=1.1)
    for v in np.arange(1.5, min(R.D - 4.5, 7.0), 0.8):
        stool(R, par, -R.W / 2 + 2.3, v, accent)
    for u, v in grid(0.0, R.W / 2 - 1.0, 1.0, R.D - 4.5, 3.0, 3.0, cap=6):
        table(R, par, u, v, 0.8, 0.8, (240, 236, 228), mat="Marble")
        chair(R, par, u - 0.65, v, (1, 0), accent)
        chair(R, par, u + 0.65, v, (-1, 0), accent)
    for v in along(0.5, R.D - 4.0, 4.0, 5):
        for k in range(5):
            u = -R.W / 2 + 0.6 + k * (R.W - 1.2) / 4
            p_ = R.p(u, v)
            ball(par, "String light", p_[0], p_[1], R.z + 2.6 - 0.2 * abs(k - 2), 0.16, (255, 214, 150), "Neon",
                 collide=False, shadow=False)


def r_golf(R, par, accent):
    R.box(par, "Putting green", -R.W / 2 + 0.8, 0.8, R.W / 2 - 0.8, R.D - 4.6, 0, 0.06, (80, 170, 70), "Grass")
    for k in range(3):
        u, v = rnd.uniform(-R.W / 2 + 2, R.W / 2 - 2), rnd.uniform(1.8, R.D - 5.6)
        q = R.p(u, v)
        vcyl(par, "Hole", q[0], q[1], R.z + 0.06, 0.005, 0.15, (20, 20, 20), collide=False)
        vcyl(par, "Flag pole", q[0], q[1], R.z, 1.4, 0.03, WHITE, "Metal", collide=False)
        R.obj(par, "Flag", u + 0.2, v, 1.15, 0.4, 0.02, 0.25, (0, 1), rnd.choice([(230, 50, 50), (250, 200, 40)]),
              "Fabric", collide=False)
    for k in range(3):
        q = R.p(rnd.uniform(-2, 2), 1.4)
        b = ball(par, "Golf ball", q[0], q[1], R.z + 0.2, 0.08, WHITE)
        b.props["Anchored"] = ("bool", False)


ROOFS = [("Roof garden", r_garden), ("Helipad", r_helipad), ("Rooftop court", r_court), ("Rooftop pool", r_pool),
         ("Rooftop bar", r_bar), ("Putting green", r_golf)]


def r_home(R, par, accent):
    """The apartments' roof garden: a pergola, a barbecue, a hot tub and benches."""
    q = R.p(-R.W / 4, R.D * 0.3)
    for e in (-1, 1):
        for g in (-1, 1):
            p_ = R.p(-R.W / 4 + e * 1.8, R.D * 0.3 + g * 1.4)
            vcyl(par, "Pergola post", p_[0], p_[1], R.z, 2.6, 0.15, (150, 104, 66), "Wood")
    for k in range(6):
        R.box(par, "Pergola slat", -R.W / 4 - 2.0, R.D * 0.3 - 1.5 + k * 0.6, -R.W / 4 + 2.0,
              R.D * 0.3 - 1.4 + k * 0.6, 2.6, 2.7, (150, 104, 66), "Wood")
    dining(R, par, -R.W / 4, R.D * 0.3, 1.8, 0.9, 4)
    R.box(par, "Barbecue", R.W / 4 - 0.6, 0.8, R.W / 4 + 0.6, 1.4, 0, 0.9, (40, 40, 44), "Metal")
    R.box(par, "Grill", R.W / 4 - 0.5, 0.85, R.W / 4 + 0.5, 1.35, 0.9, 0.93, (255, 110, 40), "Neon", collide=False)
    q = R.p(R.W / 4, R.D * 0.45)
    vcyl(par, "Hot tub", q[0], q[1], R.z, 0.8, 2.6, (150, 104, 66), "WoodPlanks")
    vcyl(par, "Hot tub water", q[0], q[1], R.z + 0.6, 0.15, 2.3, (60, 200, 230), "Neon", tr=0.3, collide=False)
    for v in (R.D * 0.65,):
        R.obj(par, "Bench", R.W / 4, v, 0, 1.8, 0.5, 0.45, (0, -1), (150, 104, 66), "Wood")

# ---- buildings: each one hollow where you can go - a ground floor, the floors its lift reaches and
# its roof - and solid in between, with the lift shaft running up through the solid part.
BUILDINGS = []                  # (name, rect, [(z, label)]) for the HUD


def ring(x0, y0, x1, y1, hole):
    """A rectangle less a rectangular hole inside it, as up to four rectangles."""
    hx0, hy0, hx1, hy1 = max(hole[0], x0), max(hole[1], y0), min(hole[2], x1), min(hole[3], y1)
    out = [(x0, y0, hx0, y1), (hx1, y0, x1, y1), (hx0, y0, hx1, hy0), (hx0, hy1, hx1, y1)]
    return [r for r in out if r[2] - r[0] > 1e-3 and r[3] - r[1] > 1e-3]


def facing(c, block):
    """The axis direction from c to the nearest edge of its block: where the street is."""
    x0, y0, x1, y1 = block
    return min([(c[0] - x0, (-1.0, 0.0)), (x1 - c[0], (1.0, 0.0)), (c[1] - y0, (0.0, -1.0)), (y1 - c[1], (0.0, 1.0))])[1]


def face_name(f):
    """Which face of an axis-aligned part looks along model direction f."""
    return {(0, -1): "Back", (0, 1): "Front", (1, 0): "Right", (-1, 0): "Left"}[(int(round(f[0])), int(round(f[1])))]


def bands(par, x0, y0, x1, y1, za, zb, glass, lit=0.75, t=0.36, name=None, skip=()):
    """Window glass round the outside of a floor, za to zb; skip leaves out faces ("x0", "x1", "y0", "y1")."""
    nm = name or ("Lit window" if rnd.random() < lit else "Window")
    e = 0.06
    ya = y0 - e + (t if "y0" not in skip else e)
    yb = y1 + e - (t if "y1" not in skip else e)
    for side, r in (("y0", (x0 - e, y0 - e, x1 + e, y0 - e + t)), ("y1", (x0 - e, y1 + e - t, x1 + e, y1 + e)),
                    ("x0", (x0 - e, ya, x0 - e + t, yb)), ("x1", (x1 + e - t, ya, x1 + e, yb))):
        if side not in skip:
            aabb(par, nm, r[0], r[1], za, r[2], r[3], zb, glass, "Glass", refl=0.15)


def toward(f):
    """The face of a rectangle that looks along f, in bands()' naming."""
    return {(0, -1): "y0", (0, 1): "y1", (1, 0): "x1", (-1, 0): "x0"}[(int(round(f[0])), int(round(f[1])))]


def storefront(par, R, t, h, door=2.2, color=(220, 220, 216), sides_glass=True):
    """A ground floor's walls: glass across the front either side of a sliding door, windows down the sides."""
    W, D = R.W, R.D
    gw = (W / 2 - door / 2 - 0.7)
    opens = {"front": [(0.0, door, 0.0, 2.75, "door"), (-(door / 2 + 0.35 + gw / 2), gw, 0.3, 3.5, "window"),
                       (door / 2 + 0.35 + gw / 2, gw, 0.3, 3.5, "window")],
             "back": []}
    for side in ("left", "right"):
        opens[side] = [(D * k, min(2.4, D * 0.2), 1.0, 3.2, "window") for k in (0.3, 0.62)] if sides_glass else []
    for side in SIDES:
        owall(R, par, side, -0.25, h, t, color, "Concrete", opens[side])
    glass_door(par, R, "front", 0.0, door, t)


def split_front(R, depth):
    """The front part of R, depth deep, where people go, and the rest behind it (or None)."""
    Dh = min(R.D, depth)
    front = R.sub(-R.W / 2, 0.0, R.W / 2, Dh)
    back = R.sub(-R.W / 2, Dh, R.W / 2, R.D) if R.D - Dh > 0.5 else None
    rect = lambda r: (min(r.p(-r.W / 2, 0)[0], r.p(r.W / 2, r.D)[0]), min(r.p(-r.W / 2, 0)[1], r.p(r.W / 2, r.D)[1]),
                      max(r.p(-r.W / 2, 0)[0], r.p(r.W / 2, r.D)[0]), max(r.p(-r.W / 2, 0)[1], r.p(r.W / 2, r.D)[1]))
    return front, rect(front), back, (rect(back) if back else None)


def solid_back(m, back, br, f, z_lo, z_hi, color, glass, levels):
    """The part of a building behind its walk-in front: solid, with windows on its three outside faces."""
    if not back:
        return
    aabb(m, "Walls", br[0], br[1], z_lo, br[2], br[3], z_hi, color, "Concrete")
    for za, zb in levels:
        bands(m, *br, za, zb, glass, skip=(toward(f),))


def office(parent, rect, block, floors, color, glass, biz, roof, fh=3.6, z0=0.1):
    x0, y0, x1, y1 = rect
    f = facing(((x0 + x1) / 2, (y0 + y1) / 2), block)
    name, theme, accent = biz
    title = name.title()
    roof_name, roof_fn = roof
    m = new(parent, "Model", title)
    t, gh = 0.3, 4.5
    zg = z0 + 0.05
    zo = zg + gh
    n_up = max(2, floors - 1)
    zr = zo + fh * n_up
    R = Room(x0, y0, x1, y1, f, zg)
    F, fr, back, br = split_front(R, 15.0)
    cd = 1.8
    q = F.p(0.0, F.D - t - (cd / 2 + 0.4))
    stops = [(zg, "G", title), (zo, "1", "Offices"), (zr, "R", roof_name)]
    hole = elevator(m, title, q[0], q[1], f, stops, cw=2.0, cd=cd, door=1.1, style="steel", vmax=11.0)
    BUILDINGS.append((title, fr, [(s[0], s[2]) for s in stops]))
    for z_, th, col, mat in ((zg, 0.3, (214, 210, 202), "Marble"), (zo, 0.35, SOFFIT, "SmoothPlastic"),
                             (zr, 0.4, (180, 180, 176), "Concrete")):
        for r in ring(*fr, hole):
            aabb(m, "Floor", r[0], r[1], z_ - th, r[2], r[3], z_, col, mat)
            if z_ == zo:
                aabb(m, "Carpet", r[0], r[1], z_, r[2], r[3], z_ + 0.02, (96, 100, 110), "Fabric", collide=False)
    levels = [(zg + 1.0, zg + 3.4), (zo + 0.9, zo + 2.9)] + [(zo + fh * k + 1.0, zo + fh * k + 2.8) for k in range(1, n_up)]
    solid_back(m, back, br, f, z0 - 0.2, zr - 0.4, color, glass, levels)
    # ground floor: the business
    storefront(m, F, t, gh - 0.35, color=color)
    fn = face_name(f)
    fascia = F.box(m, "Fascia", -F.W / 2 + 0.4, -0.3, F.W / 2 - 0.4, 0.0, 3.6, 4.2, (28, 30, 34))
    sign(fascia, name, face=fn)
    F.box(m, "Awning", -1.8, -1.3, 1.8, 0.0, 2.95, 3.1, accent, "Fabric")
    F.box(m, "Fascia light", -F.W / 2 + 0.4, -0.34, F.W / 2 - 0.4, -0.3, 3.55, 3.6, accent, "Neon", collide=False)
    theme(F.sub(-F.W / 2 + t, t, F.W / 2 - t, F.D - t), m, name, accent, gh - 0.35)
    # first floor: offices behind glass on the three outside walls
    F1 = Room(*fr, f, zo)
    for side in SIDES:
        L, c_ = (F1.W, 0.0) if side in ("front", "back") else (F1.D - 2 * t, F1.D / 2)
        owall(F1, m, side, 0.0, fh - 0.35, t, color, "Concrete",
              [] if side == "back" and back else [(c_, L - 0.8, 0.8, fh - 0.75, "window")])
    t_office(F1.sub(-F1.W / 2 + t, t, F1.W / 2 - t, F1.D - t), m, name, accent, fh - 0.35)
    # the solid floors above, round the lift shaft, and their windows
    for r in ring(*fr, hole):
        aabb(m, "Walls", r[0], r[1], zo + fh - 0.36, r[2], r[3], zr - 0.4, color, "Concrete")
    for k in range(1, n_up):
        bands(m, *fr, zo + fh * k + 1.0, zo + fh * k + 2.8, glass, skip=(toward(-np.array(f)),) if back else ())
    # the roof: the business's rooftop in front, solar panels behind
    Rr = Room(x0, y0, x1, y1, f, zr)
    aabb(m, "Parapet", x0 - 0.1, y0 - 0.1, zr - 0.4, x1 + 0.1, y1 + 0.1, zr - 0.25, (160, 160, 158), "Concrete")
    if back:
        aabb(m, "Roof", br[0], br[1], zr - 0.4, br[2], br[3], zr, (180, 180, 176), "Concrete")
        Rb = Room(*br, f, zr)
        for v in np.arange(1.2, Rb.D - 1.0, 2.4):
            Rb.obj(m, "Solar panel", 0.0, v, 0.3, Rb.W - 2.0, 1.6, 0.08, (0, 1), (24, 38, 70), "Glass", refl=0.15)
    balustrade(Rr, m)
    Fr = Room(*fr, f, zr)
    roof_fn(Fr.sub(-Fr.W / 2 + 0.3, 0.3, Fr.W / 2 - 0.3, Fr.D - 0.3), m, accent)
    return m, zr


def apartments(parent, rect, block, floors, color, glass, name, accent, fh=3.2, z0=0.1):
    x0, y0, x1, y1 = rect
    f = facing(((x0 + x1) / 2, (y0 + y1) / 2), block)
    m = new(parent, "Model", name)
    t, gh = 0.3, 4.2
    zg = z0 + 0.05
    zr = zg + gh + fh * max(3, floors - 1)
    zp = zr - 3.8
    R = Room(x0, y0, x1, y1, f, zg)
    F, fr, back, br = split_front(R, 14.0)
    cd = 1.8
    q = F.p(0.0, F.D - t - (cd / 2 + 0.4))
    stops = [(zg, "G", "Lobby"), (zp, "PH", "Penthouse"), (zr, "R", "Roof garden")]
    hole = elevator(m, name, q[0], q[1], f, stops, cw=2.0, cd=cd, door=1.1, style="gold", vmax=11.0)
    BUILDINGS.append((name, fr, [(s[0], s[2]) for s in stops]))
    for z_, th, col, mat in ((zg, 0.3, (226, 222, 214), "Marble"), (zp, 0.35, (150, 104, 66), "WoodPlanks"),
                             (zr, 0.4, (180, 180, 176), "Concrete")):
        for r in ring(*fr, hole):
            aabb(m, "Floor", r[0], r[1], z_ - th, r[2], r[3], z_, col, mat)
    levels = [(zg + 1.0, zg + 3.2)]
    z = zg + gh
    while z + fh <= zr - 0.3:
        levels.append((z + 0.9, z + 2.5))
        z += fh
    solid_back(m, back, br, f, z0 - 0.2, zr - 0.4, color, (70, 96, 110), levels)
    storefront(m, F, t, gh - 0.35, door=2.0, color=color)
    F.box(m, "Canopy", -2.4, -1.6, 2.4, 0.0, 3.0, 3.2, (240, 240, 236))
    sign(F.box(m, "Name", -2.2, -1.62, 2.2, -1.6, 3.0, 3.2, (28, 30, 34), collide=False), name, face=face_name(f))
    t_lobby(F.sub(-F.W / 2 + t, t, F.W / 2 - t, F.D - t), m, name, accent, gh - 0.35, mailboxes=True)
    for r in ring(*fr, hole):
        aabb(m, "Walls", r[0], r[1], zg + gh - 0.36, r[2], r[3], zp - 0.35, color, "Concrete")
    for za, zb in levels[1:]:
        if zb < zp - 0.4:
            bands(m, *fr, za, zb, (70, 96, 110), lit=0.7, skip=(toward(-np.array(f)),) if back else ())
    Fp = Room(*fr, f, zp)
    for side in SIDES:
        L, c_ = (Fp.W, 0.0) if side in ("front", "back") else (Fp.D - 2 * t, Fp.D / 2)
        owall(Fp, m, side, 0.0, zr - 0.4 - zp, t, color, "Concrete",
              [] if side == "back" and back else [(c_, L - 1.2, 0.5, 2.9, "window")])
    t_penthouse(Fp.sub(-Fp.W / 2 + t, t, Fp.W / 2 - t, Fp.D - t), m, name, accent, zr - 0.4 - zp)
    Rr = Room(x0, y0, x1, y1, f, zr)
    if back:
        aabb(m, "Roof", br[0], br[1], zr - 0.4, br[2], br[3], zr, (180, 180, 176), "Concrete")
    for r in ring(x0 + 1, y0 + 1, x1 - 1, y1 - 1, hole):
        aabb(m, "Roof lawn", r[0], r[1], zr, r[2], r[3], zr + 0.08, GRASS, "Grass")
    balustrade(Rr, m)
    Fr = Room(*fr, f, zr)
    r_home(Fr.sub(-Fr.W / 2 + 0.5, 0.5, Fr.W / 2 - 0.5, Fr.D - 0.5, z=zr + 0.08), m, accent)
    return m, zr


TOWER_NAMES = ["Aurora", "Meridian", "Zenith", "Halcyon", "Solstice", "Orion", "Vertex", "Lumen", "Cobalt", "Nimbus",
               "Helix", "Prism", "Atlas", "Summit", "Ember", "Lyra", "Polaris"]
CLEAR_GLAZING = dict(color=(186, 214, 226), mat="Glass", tr=0.4, refl=0.08, shadow=False)


def tower(parent, cx, cy, w, d, h, glass, frame, front, name, accent, lobby=0, lounge=0, z0=0.1, crown=(120, 230, 255),
          car="gold"):
    m = new(parent, "Model", name)
    pod, t = 9.0, 0.35
    tiers = [(1.0, 0.6), (0.78, 0.84), (0.56, 1.0)] if h > 100 else [(1.0, 0.75), (0.7, 1.0)] if h > 60 else [(1.0, 1.0)]
    tops = [z0 + h * frac for _, frac in tiers]
    # sky lounges: the top of the last tier, and on the tallest tower the top of the one below too
    rooms = [len(tiers) - 1] + ([len(tiers) - 2] if h > 200 else [])
    zl = {i: tops[i] - 6.2 for i in rooms}
    zg = z0 + 0.05
    names = {}
    stops = [(zg, "L", "Lobby")]
    for k, i in enumerate(sorted(rooms)):
        title, fn = SKY_LOUNGES[(lounge + k) % len(SKY_LOUNGES)]
        names[i] = (title, fn)
        floor_no = int(round((zl[i] - z0) / 4.0))
        stops.append((zl[i], str(floor_no), title))
    px0, py0, px1, py1 = cx - w / 2 - 4, cy - d / 2 - 4, cx + w / 2 + 4, cy + d / 2 + 4
    hole = elevator(m, name, cx, cy, front, stops, cw=2.6, cd=2.2, door=1.3, style=car, vmax=13.0,
                    top=tops[max(rooms)] - 0.05, shaft_lights=True, shaft_color=(60, 64, 70))
    BUILDINGS.append((name, (px0, py0, px1, py1), [(s[0], s[2]) for s in stops]))

    # the podium: a double-height lobby behind glass
    P = Room(px0, py0, px1, py1, front, zg)
    for r in ring(px0, py0, px1, py1, hole):
        aabb(m, "Floor", r[0], r[1], zg - 0.3, r[2], r[3], zg, (226, 222, 214), "Marble")
        aabb(m, "Podium roof", r[0], r[1], z0 + pod - 0.4, r[2], r[3], z0 + pod, rnd.choice(CONC), "Concrete")
    opens = {s: [((0.0 if s in ("front", "back") else P.D / 2), (P.W if s in ("front", "back") else P.D) - 1.4,
                  0.35, 4.6, "window")] for s in SIDES}
    opens["front"] = [(0.0, 2.6, 0.0, 2.75, "door"), (-(P.W / 4 + 0.65), P.W / 2 - 2.0, 0.35, 4.6, "window"),
                      (P.W / 4 + 0.65, P.W / 2 - 2.0, 0.35, 4.6, "window")]
    for side in SIDES:
        owall(P, m, side, -0.25, pod - 0.45 - 0.05, t, rnd.choice(CONC), "Concrete", opens[side], glass=CLEAR_GLAZING)
    glass_door(m, P, "front", 0.0, 2.6, t, h=2.7)
    fascia = P.box(m, "Name", -min(6.0, P.W / 2 - 1), -0.12, min(6.0, P.W / 2 - 1), 0.0, 5.2, 6.6, (24, 26, 30))
    sign(fascia, name.upper(), face=face_name(front))
    P.box(m, "Canopy", -2.8, -2.2, 2.8, 0.0, 3.1, 3.3, frame, "Metal")
    t_grand_lobby(P.sub(-P.W / 2 + t, t, P.W / 2 - t, P.D - t), m, name.upper(), accent, pod - 0.55, lobby)

    # the tiers, hollow round the shaft
    zb = z0 + pod
    for i, (scale, frac) in enumerate(tiers):
        tw, td, zt = w * scale, d * scale, tops[i]
        tx0, ty0, tx1, ty1 = cx - tw / 2, cy - td / 2, cx + tw / 2, cy + td / 2
        solid_top = zl[i] - 0.4 if i in zl else zt
        nm = "Lit window" if rnd.random() < 0.7 else "Window"
        for r in ring(tx0, ty0, tx1, ty1, hole):
            aabb(m, nm, r[0], r[1], zb, r[2], r[3], solid_top, glass, "Glass", refl=0.22)
        z = zb + 4.0
        while z < solid_top - 1.5:
            for r in ((tx0 - 0.25, ty0 - 0.25, hole[0], ty1 + 0.25), (hole[2], ty0 - 0.25, tx1 + 0.25, ty1 + 0.25)):
                aabb(m, "Spandrel", r[0], r[1], z - 0.45, r[2], r[3], z + 0.45, frame, "Metal")
            z += 4.0
        if i in zl:
            L = Room(tx0, ty0, tx1, ty1, front, zl[i])
            for r in ring(tx0, ty0, tx1, ty1, hole):
                aabb(m, "Floor", r[0], r[1], zl[i] - 0.4, r[2], r[3], zl[i], (60, 58, 56), "Marble")
            hh = zt - zl[i]
            skywalk = h > 200 and i == len(tiers) - 1
            for side in SIDES:
                span = L.W if side in ("front", "back") else L.D - 0.5
                c_ = 0.0 if side in ("front", "back") else L.D / 2
                opens = [(c_, span - 0.5, 0.25, hh - 0.35, "window")]
                if skywalk and side == "front":
                    opens = [(-(span / 4 + 1.0), span / 2 - 2.25, 0.25, hh - 0.35, "window"), (0.0, 3.0, 0.0, 2.8, "door"),
                             (span / 4 + 1.0, span / 2 - 2.25, 0.25, hh - 0.35, "window")]
                owall(L, m, side, 0.0, hh, 0.25, frame, "Metal", opens, glass=CLEAR_GLAZING)
                s0, s1 = (-L.W / 2, L.W / 2) if side in ("front", "back") else (0.25, L.D - 0.25)
                for s in np.arange(s0 + 3.5, s1 - 1.0, 3.5):
                    if not (skywalk and side == "front" and abs(s) < 2.0):
                        side_box(L, m, "Mullion", side, s - 0.05, s + 0.05, 0.0, hh, 0.3, frame, "Metal")
            title, fn = names[i]
            fn(L.sub(-L.W / 2 + 0.25, 0.25, L.W / 2 - 0.25, L.D - 0.25), m, title.upper() + "  ·  " + name.upper(), accent,
               hh - 0.1, 2.2)
            for k in range(3):
                lamp_panel(L, m, (k - 1) * L.W / 3, L.D * 0.25, hh - 0.02, w=1.2, d=0.4, rng=20, brightness=0.6)
            if skywalk:                 # a glass box over the edge with a glass floor
                L.box(m, "Skywalk floor", -1.5, -3.2, 1.5, 0.0, -0.12, 0.0, (200, 230, 240), "Glass", tr=0.55, refl=0.1)
                L.box(m, "Skywalk frame", -1.6, -3.3, 1.6, -3.2, -0.2, 2.9, frame, "Metal")
                for e in (-1, 1):
                    L.box(m, "Skywalk glass", e * 1.5 - 0.04, -3.2, e * 1.5 + 0.04, 0.0, 0.0, 2.8, **CLEAR_GLAZING)
                    L.box(m, "Skywalk frame", e * 1.6 - 0.1, -3.3, e * 1.6, 0.0, -0.2, 2.9, frame, "Metal")
                L.box(m, "Skywalk glass", -1.5, -3.2, 1.5, -3.12, 0.0, 2.8, **CLEAR_GLAZING)
                L.box(m, "Skywalk roof", -1.6, -3.3, 1.6, 0.0, 2.8, 2.95, (200, 230, 240), "Glass", tr=0.5)
                BUILDINGS[-1][2].append((zl[i] + 0.01, "Skywalk"))
        last = i == len(tiers) - 1
        for r in ([(tx0 - 0.3, ty0 - 0.3, tx1 + 0.3, ty1 + 0.3)] if last else
                  ring(tx0 - 0.3, ty0 - 0.3, tx1 + 0.3, ty1 + 0.3, hole)):
            aabb(m, "Roof", r[0], r[1], zt, r[2], r[3], zt + 0.8, frame, "Metal")
        zb = zt + 0.8
    tw, td = w * tiers[-1][0], d * tiers[-1][0]
    x0, y0, x1, y1 = cx - tw / 2 - 0.35, cy - td / 2 - 0.35, cx + tw / 2 + 0.35, cy + td / 2 + 0.35
    for r in ((x0, y0, x1, y0 + 0.5), (x0, y1 - 0.5, x1, y1), (x0, y0 + 0.5, x0 + 0.5, y1 - 0.5),
              (x1 - 0.5, y0 + 0.5, x1, y1 - 0.5)):
        aabb(m, "Crown", r[0], r[1], zb, r[2], r[3], zb + 1.2, crown, "Neon", collide=False)
    vcyl(m, "Antenna", cx, cy, zb, max(6, h * 0.1), 0.5, (200, 200, 205), "Metal")
    ball(m, "Beacon", cx, cy, zb + max(6, h * 0.1), 1.0, (255, 40, 40), "Neon", collide=False)
    return m, stops


HOUSE_WALL = [(236, 228, 214), (214, 196, 170), (190, 210, 220), (226, 212, 190), (204, 220, 198), (240, 236, 228),
              (222, 190, 170)]
HOUSE_ROOF = [(150, 70, 52), (90, 92, 98), (60, 66, 74), (170, 96, 64), (120, 64, 50)]
SOFAS = [(110, 120, 140), (150, 90, 70), (90, 120, 100), (200, 190, 170), (70, 70, 80), (160, 120, 160)]
STREETS_ = ["Maple", "Jasmine", "Banyan", "Lotus", "Cedar", "Mango", "Lake View", "Hill"]


def house(parent, x, y, f, setback, z0=0.0, number=1):
    """A house at (x, y) whose front faces f (an axis unit vector towards the street), and its garden."""
    f = np.array(f, float)
    a = np.array([-f[1], f[0]])
    w, d = rnd.uniform(10.5, 12.5), rnd.uniform(8.6, 10.0)
    storeys = rnd.choice([1, 1, 2])
    H = 3.2 * storeys
    c = np.array([x, y])
    p0, p1 = c - a * w / 2 - f * d / 2, c + a * w / 2 + f * d / 2
    rect = (min(p0[0], p1[0]), min(p0[1], p1[1]), max(p0[0], p1[0]), max(p0[1], p1[1]))
    m = new(parent, "Model", "House")
    R = Room(*rect, f, z0 + 0.15)
    t, wc = 0.2, rnd.choice(HOUSE_WALL)
    W, D = R.W, R.D
    vp = D * 0.55                                   # living room in front, kitchen and bedroom behind
    du = W / 2 - 1.7                                # front and back doors
    usep = W / 2 - 3.4                              # kitchen | bedroom
    R.box(m, "Floor", -W / 2, 0, W / 2, D, -0.3, 0.0, rnd.choice([(150, 104, 66), (180, 140, 100), (120, 84, 60)]),
          "WoodPlanks")
    opens = {"front": [(du, 1.0, 0.0, 2.15, "door"), (-W / 4, 1.8, 0.9, 2.3, "window")],
             "back": [(du, 1.0, 0.0, 2.15, "door"), (-W / 2 + 1.4, 1.4, 0.9, 2.3, "window")],
             "left": [(D * 0.3, 1.4, 1.0, 2.3, "window")], "right": [(D * 0.3, 1.4, 1.0, 2.3, "window")]}
    if storeys == 2:
        opens["front"] += [(-W / 4, 1.8, 4.1, 5.5, "window"), (W / 4, 1.8, 4.1, 5.5, "window")]
        opens["back"] += [(W / 4, 1.6, 4.1, 5.5, "window")]
        for s in ("left", "right"):
            opens[s].append((D * 0.5, 1.4, 4.2, 5.5, "window"))
    for side in SIDES:
        owall(R, m, side, -0.3, H, t, wc, "Concrete", opens[side], glass=dict(GLAZING, tr=0.35))
    swing_door(m, R, "front", du, 1.0, t, rnd.choice([(120, 80, 50), (40, 70, 110), (160, 40, 40), (40, 90, 60)]))
    swing_door(m, R, "back", du, 1.0, t)
    plaque = R.box(m, "House number", du + 0.75, -0.04, du + 1.15, 0.0, 1.6, 1.85, (30, 34, 40))
    sign(plaque, str(number), face=face_name(f), style="button")
    # partitions
    pc = (246, 244, 238)
    for s0, s1 in ((-W / 2 + t, -W / 4 - 0.45), (-W / 4 + 0.45, du - 0.5), (du + 0.5, W / 2 - t)):
        R.box(m, "Partition", s0, vp - 0.05, s1, vp + 0.05, 0.0, 3.0, pc)
    for g in (-W / 4, du):
        R.box(m, "Partition", g - 0.45 if g < 0 else g - 0.5, vp - 0.05, g + 0.45 if g < 0 else g + 0.5, vp + 0.05, 2.15,
              3.0, pc)
    R.box(m, "Partition", usep - 0.05, vp + 0.05, usep + 0.05, D - t, 0.0, 3.0, pc)
    # living room
    sc = rnd.choice(SOFAS)
    lv = vp / 2
    tv(R, m, -W / 2 + t + 0.3, lv, (1, 0), 1.3, rnd.choice(["NEWS", "CRICKET LIVE", "CARTOONS", "GLASS CITY TV"]),
       rnd.choice(ART))
    rug(R, m, -W / 2 + t + 1.9, lv, 2.0, 2.6, rnd.choice(ART))
    table(R, m, -W / 2 + t + 1.9, lv, 0.6, 1.0, (150, 104, 66), h=0.4)
    sofa(R, m, -W / 2 + t + 3.3, lv, (-1, 0), w=2.2, color=sc)
    floor_lamp(R, m, -W / 2 + t + 3.4, lv + 1.5)
    shelf(R, m, (-W / 4 + 0.45 + du - 0.5) / 2, vp - 0.27, (0, -1), w=1.6, h=1.9)
    um = (-W / 2 + t + 4.2 + du - 0.9) / 2
    dining(R, m, um, lv - 0.2, 1.3, 0.8, 4, chairs=rnd.choice([(150, 104, 66), (40, 40, 44), (230, 230, 226)]))
    plant(R, m, W / 2 - t - 0.4, t + 0.4, 1.2)
    lamp_panel(R, m, -W / 4, lv, 3.15 if storeys == 2 else H - 0.02, rng=14, brightness=0.6)
    # kitchen
    counter(R, m, W / 2 - t - 0.65, vp + 0.25, W / 2 - t, D - t - 1.4, (240, 240, 236), rnd.choice([(60, 62, 66),
                                                                                                    (230, 226, 218)]))
    R.box(m, "Hob", W / 2 - t - 0.55, vp + 0.5, W / 2 - t - 0.1, vp + 1.1, 0.95, 0.965, (20, 20, 22), "Glass",
          collide=False)
    R.box(m, "Sink", W / 2 - t - 0.55, vp + 1.6, W / 2 - t - 0.1, vp + 2.1, 0.95, 0.96, (180, 184, 188), "Metal",
          collide=False)
    fridge(R, m, usep + 0.45, D - t - 0.45, (1, 0))
    lamp_panel(R, m, (usep + W / 2) / 2, (vp + D) / 2, 3.15 if storeys == 2 else H - 0.02, rng=12, brightness=0.6)
    if storeys == 1:
        bu = (-W / 2 + usep) / 2 + 0.3
        bed(R, m, bu, D - t - 1.1, (0, -1), w=1.6, L=2.1, color=rnd.choice(ART))
        R.obj(m, "Nightstand", bu - 1.15, D - t - 0.3, 0, 0.5, 0.4, 0.55, (0, -1), (150, 104, 66), "Wood")
        R.obj(m, "Wardrobe", -W / 2 + t + 0.35, vp + 1.3, 0, 1.6, 0.6, 2.1, (1, 0), (236, 232, 224), "Wood")
        lamp_panel(R, m, bu, (vp + D) / 2, H - 0.02, w=0.7, d=0.7, lit=False)
    else:
        # stairs up the left wall of the back half, and the bedroom upstairs
        sx0, sx1 = -W / 2 + t, -W / 2 + t + 1.0
        v_a, v_b = vp + 0.2, D - t
        n = 13
        for k in range(n):
            va = v_a + (v_b - v_a) * k / n
            R.box(m, "Stair", sx0, va, sx1, va + (v_b - v_a) / n + 0.02, 0.0, 3.2 * (k + 1) / n, pc, "Wood")
        R.box(m, "Stair rail", sx1 - 0.04, v_a, sx1, v_b, 1.0, 1.05 + 3.2 * 0.5, (150, 104, 66), "Wood", collide=False)
        for r in ((-W / 2 + t, t, W / 2 - t, v_a - 0.05), (sx1 + 0.05, v_a - 0.05, W / 2 - t, D - t)):
            R.box(m, "Upper floor", r[0], r[1], r[2], r[3], 2.95, 3.2, (150, 104, 66), "WoodPlanks")
        R.box(m, "Landing rail", sx1 + 0.05, v_a - 0.05, sx1 + 0.1, D - t - 1.2, 3.2, 4.2, (150, 104, 66), "Wood")
        U = R.sub(-W / 2 + t, t, W / 2 - t, D - t, z=R.z + 3.2)
        bed(U, m, U.W / 2 - 1.15, U.D * 0.6, (-1, 0), w=1.6, L=2.1, color=rnd.choice(ART))
        shelf(R, m, (sx1 + usep) / 2, D - t - 0.25, (0, -1), w=1.6, h=1.9)
        R.obj(m, "Wardrobe", W / 2 - t - 0.35, 1.5, 3.2, 1.6, 0.6, 2.1, (-1, 0), (236, 232, 224), "Wood")
        desk(U, m, -U.W / 4, 0.75, (0, -1), 1.2, screen=rnd.choice(ART))
        rug(U, m, 0.0, U.D * 0.4, 2.6, 2.0, rnd.choice(ART))
        lamp_panel(U, m, 0.0, U.D * 0.4, 3.15, rng=12, brightness=0.55)
    # roof, chimney, drive
    rc = rnd.choice(HOUSE_ROOF)
    yaw = math.atan2(f[1], f[0])
    for sgn in (1, -1):
        q = c + f * sgn * (d / 4 + 0.25)
        ramp(m, "Roof", q[0], q[1], z0 + 0.15 + H, d / 2 + 0.5, w + 0.8, 2.2, yaw + (math.pi if sgn > 0 else 0), rc, "Slate")
    if rnd.random() < 0.4:
        q = c - f * (d / 4) + a * (w / 2 - 1.5)
        ybox(m, "Chimney", q[0], q[1], z0 + H, 0.8, 0.8, 2.8, yaw + math.pi / 2, (150, 96, 80), "Concrete")
    drive = c + f * (d / 2 + setback / 2) + a * (w / 2 - 1.7)
    ybox(m, "Driveway", drive[0], drive[1], z0 - 0.14, 3.2, setback, 0.2, yaw + math.pi / 2, (184, 180, 172), "Concrete")
    garden(m, R, rnd.choice(GARDENS))
    return drive


def garden(m, R, kind):
    """Something in the back garden: v beyond D is behind the house."""
    D = R.D
    g = R.sub(-R.W / 2 + 0.5, D + 1.0, R.W / 2 - 0.5, D + 9.0, z=R.z - 0.15)
    if kind == "pool":
        g.box(m, "Pool deck", -3.0, 1.0, 3.0, 7.8, -0.1, 0.06, (214, 206, 190), "Slate")
        g.box(m, "Pool", -2.2, 1.6, 2.2, 7.2, 0.02, 0.08, (40, 170, 220), "Glass", tr=0.2, refl=0.3, collide=False)
        for u in (-2.6, 2.6):
            g.obj(m, "Lounger", u + (0.8 if u > 0 else -0.8), 4.0, 0, 0.7, 1.9, 0.35, (0, -1), WHITE, "Fabric")
    elif kind == "trampoline":
        q = g.p(0.0, 4.0)
        for k in range(4):
            ang = k * math.pi / 2 + 0.4
            vcyl(m, "Trampoline leg", q[0] + 1.6 * math.cos(ang), q[1] + 1.6 * math.sin(ang), g.z, 0.8, 0.1,
                 (40, 40, 44), "Metal")
        vcyl(m, "Trampoline frame", q[0], q[1], g.z + 0.75, 0.1, 3.8, (40, 120, 220), "Fabric")
        vcyl(m, "Trampoline", q[0], q[1], g.z + 0.8, 0.08, 3.3, (24, 24, 28), "Fabric")
    elif kind == "bbq":
        dining(g, m, 0.0, 4.5, 1.8, 0.8, 4, color=(150, 104, 66), chairs=(150, 104, 66))
        g.box(m, "Barbecue", 2.2, 1.2, 3.2, 1.8, 0, 0.9, (40, 40, 44), "Metal")
        g.box(m, "Grill", 2.3, 1.25, 3.1, 1.75, 0.9, 0.93, (255, 110, 40), "Neon", collide=False)
    elif kind == "swings":
        for e in (-1, 1):
            g.box(m, "Swing frame", e * 1.6 - 0.08, 3.4, e * 1.6 + 0.08, 3.56, 0, 2.4, (200, 60, 60), "Metal")
        g.box(m, "Swing bar", -1.7, 3.4, 1.7, 3.56, 2.4, 2.55, (200, 60, 60), "Metal")
        for u in (-0.7, 0.7):
            q = g.p(u, 3.48)
            st = ybox(m, "Swing", q[0], q[1], g.z + 0.5, 0.5, 0.4, 0.06, g.phi(0, -1), (40, 40, 44), cls="Seat")
            st.props["Disabled"] = ("bool", False)
    elif kind == "hottub":
        q = g.p(0.0, 3.5)
        vcyl(m, "Hot tub", q[0], q[1], g.z, 0.8, 2.4, (150, 104, 66), "WoodPlanks")
        vcyl(m, "Hot tub water", q[0], q[1], g.z + 0.6, 0.15, 2.1, (60, 200, 230), "Neon", tr=0.3, collide=False)
        g.box(m, "Deck", -2.0, 5.0, 2.0, 7.0, -0.05, 0.1, (150, 104, 66), "WoodPlanks")
    elif kind == "veg":
        for u in (-2.4, 0.0, 2.4):
            g.box(m, "Raised bed", u - 0.8, 2.0, u + 0.8, 6.0, 0, 0.45, (120, 84, 60), "WoodPlanks")
            g.box(m, "Soil", u - 0.7, 2.1, u + 0.7, 5.9, 0.45, 0.5, (90, 66, 46), "Grass")
            for v in (2.8, 4.0, 5.2):
                q = g.p(u, v)
                ball(m, "Veg", q[0], q[1], g.z + 0.7, 0.45, rnd.choice([(70, 140, 60), (230, 70, 50), (240, 160, 40)]),
                     "Grass", collide=False)
    elif kind == "shed":
        g.box(m, "Shed", -1.5, 4.0, 1.5, 6.5, 0, 2.3, (150, 104, 66), "WoodPlanks")
        g.box(m, "Shed door", -0.5, 3.96, 0.5, 4.0, 0, 1.9, (90, 60, 40), "Wood")
        g.box(m, "Shed roof", -1.7, 3.8, 1.7, 6.7, 2.3, 2.45, (70, 70, 76), "Slate")


GARDENS = ["pool", "trampoline", "bbq", "swings", "hottub", "veg", "shed"]


# ---- suburbs: two blocks of houses down the west side
suburbs = new(city, "Folder", "Suburbs")
house_no = 0
car_pad(-33.0, 160.0, 0.0, -28.0, 165.0, 0.0)
for key, (x0, y0, x1, y1) in BLOCKS.items():
    if not key.startswith(("C1R", "C2R")):
        continue
    for f, xh in (((-1.0, 0.0), x0 + SW + 7 + 4.5), ((1.0, 0.0), x1 - SW - 7 - 4.5)):
        for y in np.arange(y0 + SW + 10, y1 - SW - 9, 20):
            fx0, fx1 = (xh - 6, xh + 13) if f[0] > 0 else (xh - 13, xh + 6)      # house and driveway
            if not fits(fx0, y - 7, fx1, y + 7, 2.0):
                continue
            house_no += 1
            drive = house(suburbs, xh, y, f, 7.0, number=house_no)
            if rnd.random() < 0.5:
                tree(suburbs, np.array([xh - f[0] * 10, y + rnd.uniform(-5, 5)]), 6 + rnd.random() * 3,
                     2.4 + rnd.random(), SPECIES[rnd.choice([0, 1, 2, 3])], n=4)
            if rnd.random() < 0.14:
                parked(drive[0], drive[1], 0.06, math.atan2(f[1], f[0]))
for q in ((-58.0, 100.0), (-140.0, -60.0), (-58.0, 200.0), (-141.0, 160.0), (-58.0, -130.0), (-141.0, 250.0)):
    coin(q[0], q[1], 1.0)

# ---- midtown: mid-rise offices south of the mall
midtown = new(city, "Folder", "Midtown")
car_pad(85.3, -103.0, 0.1, 85.3, -112.0, -math.pi / 2)
biz = rnd.sample(BUSINESS, len(BUSINESS))
n_biz = 0
for key in ("C3R1", "C3R2", "C4R1", "C4R2"):
    x0, y0, x1, y1 = BLOCKS[key]
    paved(midtown, "Paving", x0 + SW, y0 + SW, x1 - SW, y1 - SW, 0.1, 0.25, PAVE, "Slate")
    for c in lots(*BLOCKS[key], 22):
        fx0, fy0 = c[0] + rnd.uniform(1, 3), c[1] + rnd.uniform(1, 3)
        fx1, fy1 = c[2] - rnd.uniform(1, 3), c[3] - rnd.uniform(1, 3)
        if fits(fx0, fy0, fx1, fy1):
            office(midtown, (fx0, fy0, fx1, fy1), BLOCKS[key], rnd.randint(4, 9), rnd.choice(CONC), rnd.choice(GLASSES),
                   biz[n_biz % len(biz)], ROOFS[n_biz % len(ROOFS)])
            n_biz += 1
for q in ((30.0, -130.0), (118.0, -134.0), (30.0, -210.0), (118.0, -210.0)):
    coin(q[0], q[1], 1.1)

# ---- downtown: towers round a plaza with a fountain
downtown = new(city, "Folder", "Downtown")
PLAZA = (180.0, 18.0, 236.0, 74.0)
RESERVED.append(PLAZA)
car_pad(183.0, 52.0, 0.12, 175.5, 52.0, math.pi)
first = True
n_tower = 0
SPIRE = None
ACCENTS = [(60, 200, 255), (255, 120, 220), (250, 190, 60), (120, 230, 160), (180, 120, 255), (255, 110, 80)]
for key in ("C5R1", "C5R2", "C5R3", "C6R1", "C6R2", "C6R3"):
    x0, y0, x1, y1 = BLOCKS[key]
    paved(downtown, "Paving", x0 + SW, y0 + SW, x1 - SW, y1 - SW, 0.1, 0.25, PAVE, "Slate")
    for c in lots(*BLOCKS[key], 30):
        if not fits(*c):
            continue
        cw, ch = c[2] - c[0], c[3] - c[1]
        w, d = cw - 8 - rnd.uniform(1, 4), ch - 8 - rnd.uniform(1, 4)
        w, d = min(w, 28), min(d, 28)
        cx, cy = (c[0] + c[2]) / 2, (c[1] + c[3]) / 2
        front = facing((cx, cy), BLOCKS[key])
        if key == "C6R3" and first:
            first = False
            tower(downtown, cx, cy, w, d, 232, (36, 70, 96), (230, 232, 234), front, "Glass Spire", (255, 120, 220),
                  lobby=0, lounge=1, crown=(255, 120, 220), car="night")
            SPIRE = (cx, cy, d if abs(front[1]) > 0.5 else w, front)
            continue
        near = math.hypot(cx - 208, cy - 46)
        h = max(50, rnd.uniform(130, 190) - near * 0.45 + rnd.uniform(-20, 20))
        tower(downtown, cx, cy, w, d, h, rnd.choice(GLASSES), rnd.choice(FRAMES), front,
              TOWER_NAMES[n_tower % len(TOWER_NAMES)] + " Tower", ACCENTS[n_tower % len(ACCENTS)], lobby=n_tower % 3,
              lounge=n_tower + 2, car=("gold", "steel", "night")[n_tower % 3])
        n_tower += 1
plaza = new(downtown, "Model", "Plaza")
aabb(plaza, "Plaza", *PLAZA[:2], 0.0, *PLAZA[2:], 0.13, (190, 186, 180), "Granite")
fx, fy = 208.0, 46.0
vcyl(plaza, "Fountain basin", fx, fy, 0.13, 0.7, 16, (200, 196, 190), "Granite")
vcyl(plaza, "Fountain water", fx, fy, 0.13, 0.62, 15, (70, 170, 210), "Glass", tr=0.25, refl=0.3, collide=False)
vcyl(plaza, "Fountain column", fx, fy, 0.13, 3.0, 2.4, (200, 196, 190), "Granite")
vcyl(plaza, "Fountain bowl", fx, fy, 2.7, 0.4, 6.5, (200, 196, 190), "Granite")
vcyl(plaza, "Fountain jet", fx, fy, 3.1, 3.2, 0.7, (170, 225, 255), "Glass", tr=0.35, collide=False)
for k in range(8):
    ang = k * math.pi / 4
    q = np.array([fx, fy]) + 11.5 * np.array([math.cos(ang), math.sin(ang)])
    seat(plaza, q[0], q[1], 0.13, ang + math.pi / 2, color=(120, 90, 64), back=True, w=1.6)
for q in ((186.0, 24.0), (230.0, 24.0), (230.0, 68.0)):
    vcyl(plaza, "Planter", q[0], q[1], 0.13, 0.6, 3.4, (160, 156, 150), "Concrete")
    tree(plaza, np.array(q), 7.5, 2.6, SPECIES[3], n=4, z0=0.7)
led = wall(plaza, "Plaza screen", np.array([188.0, 73.0]), np.array([228.0, 73.0]), 0.13, 9.0, 0.6, (18, 26, 60), "Neon")
sign(led, "GLASS CITY", style="led", accent=(60, 200, 255))
for ang in (0.4, 1.9, 3.5, 5.0):
    coin(fx + 9 * math.cos(ang), fy + 9 * math.sin(ang), 1.2)

# ---- uptown: bright apartment blocks along the north edge
uptown = new(city, "Folder", "Uptown")
car_pad(70.0, 243.0, 0.1, 79.0, 243.0, 0.0)
HOMES = ["Jasmine Court", "Banyan Heights", "Lotus Residency", "Skyline Flats", "Marigold House", "Cedar Point",
         "Coral Apartments", "Indigo Lofts", "Peacock Towers", "Monsoon Villas", "Tamarind Place", "Bluebell Row"]
n_home = 0
for key in ("C34R5", "C56R5"):
    x0, y0, x1, y1 = BLOCKS[key]
    paved(uptown, "Paving", x0 + SW, y0 + SW, x1 - SW, y1 - SW, 0.1, 0.25, PAVE, "Slate")
    for c in lots(*BLOCKS[key], 24):
        fx0, fy0, fx1, fy1 = c[0] + 1.5, c[1] + 1.5, c[2] - 1.5, c[3] - 1.5
        if fits(fx0, fy0, fx1, fy1):
            apartments(uptown, (fx0, fy0, fx1, fy1), BLOCKS[key], rnd.randint(6, 13), rnd.choice(BRIGHT), (70, 96, 110),
                       HOMES[n_home % len(HOMES)], ACCENTS[n_home % len(ACCENTS)])
            n_home += 1
for q in ((40.0, 266.0), (120.0, 266.0), (200.0, 266.0), (280.0, 266.0)):
    coin(q[0], q[1], 1.1)

# ---- the mall car park, behind the boulevard
lot_f = new(city, "Folder", "Mall car park")
LOT = (-4.7, -81.0, 65.3, -38.0)
paved(lot_f, "Car park", *LOT, 0.08, 0.2, (66, 68, 72), "Asphalt")
car_pad(-1.5, -68.5, 0.08, 6.5, -68.5, 0.0)
ROWS = [(-78.5, -73.0, math.pi / 2), (-64.0, -58.5, -math.pi / 2), (-58.5, -53.0, math.pi / 2),
        (-44.0, -38.5, -math.pi / 2)]
for ya, yb, head_ in ROWS:
    for x in np.arange(4.0, 61.0, 3.0):
        aabb(lot_f, "Bay line", x - 0.06, ya, 0.08, x + 0.06, yb, 0.092, MARK, collide=False, shadow=False, query=False)
bays = [(x + 1.5, (ya + yb) / 2, head_) for ya, yb, head_ in ROWS for x in np.arange(4.0, 58.0, 3.0)]
for x, y, head_ in rnd.sample(bays, 7):
    parked(x, y, 0.08, head_)
for q in ((-2.5, -42.0), (-2.5, -78.0), (63.0, -42.0), (63.0, -78.0)):
    street_lamp(np.array(q), (1, 0) if q[0] < 0 else (-1, 0), z0=0.08)
psign = wall(lot_f, "Car park sign", np.array([-3.4, -46.0]), np.array([-3.4, -50.0]), 2.6, 1.6, 0.2, (30, 70, 160))
sign(psign, "P  PARKING", face="Back")
vcyl(lot_f, "Sign post", -3.4, -48.0, 0.08, 2.6, 0.15, (70, 74, 78), "Metal")
coin(30.0, -68.5)
coin(30.0, -49.0)

# ---- Central Park: a lake with a jetty and rowing boats, paths, a gazebo and a playground
park = new(city, "Folder", "Park")
floating = new(park, "Folder", "Floating")
PX0, PY0, PX1, PY1 = BLOCKS["C4R3"]
for r in ((lx0 - 0.8, ly0 - 0.8, lx1 + 0.8, ly0), (lx0 - 0.8, ly1, lx1 + 0.8, ly1 + 0.8), (lx0 - 0.8, ly0, lx0, ly1),
          (lx1, ly0, lx1 + 0.8, ly1)):
    aabb(park, "Lake rim", *r[:2], -0.3, *r[2:], 0.1, (196, 190, 178), "Slate")
loop_ = (lx0 - 7.0, ly0 - 7.0, lx1 + 7.0, ly1 + 7.0)
PATHS_PARK = [(loop_[0], loop_[1], loop_[2], loop_[1] + 3), (loop_[0], loop_[3] - 3, loop_[2], loop_[3]),
              (loop_[0], loop_[1] + 3, loop_[0] + 3, loop_[3] - 3), (loop_[2] - 3, loop_[1] + 3, loop_[2], loop_[3] - 3),
              (116.5, loop_[3], 119.5, PY1 - SW), (PX0 + SW, 41.5, loop_[0], 44.5), (loop_[2], 41.5, PX1 - SW, 44.5),
              (116.5, -24.0, 119.5, loop_[1])]
for r in PATHS_PARK:
    paved(park, "Path", *r, 0.06, 0.2, (204, 196, 180), "Slate")
aabb(park, "Jetty", 116.0, loop_[1] + 3, -0.1, 120.0, 32.0, 0.14, (150, 104, 66), "WoodPlanks")
for q in ((116.3, 25.0), (119.7, 25.0), (116.3, 31.6), (119.7, 31.6)):
    vcyl(park, "Jetty post", q[0], q[1], -3.6, 3.7, 0.25, (120, 84, 54), "Wood")
for q in ((106.0, 40.0), (128.0, 52.0)):
    aabb(floating, "Rowboat", q[0] - 0.7, q[1] - 1.6, -0.5, q[0] + 0.7, q[1] + 1.6, -0.08, (196, 70, 50), "WoodPlanks")
for k, q in enumerate(((100.0, 13.5), (130.0, 13.5), (100.0, 72.5), (130.0, 72.5), (87.0, 30.0), (87.0, 58.0),
                       (149.0, 30.0), (149.0, 58.0))):
    phi = (0.0, 0.0, math.pi, math.pi, -math.pi / 2, -math.pi / 2, math.pi / 2, math.pi / 2)[k]
    seat(park, q[0], q[1], 0.0, phi, color=(120, 86, 58), back=True, w=1.6)
gz = (100.0, -4.0)
vcyl(park, "Gazebo floor", *gz, -0.1, 0.4, 9, (150, 104, 66), "WoodPlanks")
for k in range(6):
    ang = k * math.pi / 3
    vcyl(park, "Gazebo post", gz[0] + 3.9 * math.cos(ang), gz[1] + 3.9 * math.sin(ang), 0.3, 3.0, 0.25, WHITE, "Wood")
vcyl(park, "Gazebo roof", *gz, 3.3, 0.3, 10, (110, 60, 50), "Slate")
vcyl(park, "Gazebo roof", *gz, 3.6, 0.5, 6, (110, 60, 50), "Slate")
ball(park, "Gazebo finial", gz[0], gz[1], 4.3, 0.6, (230, 200, 120), "Metal")
pg = (136.0, -4.0)
aabb(park, "Sandpit", pg[0] - 7, pg[1] - 6, -0.1, pg[0] + 7, pg[1] + 6, 0.05, (230, 210, 160), "Sand")
aabb(park, "Slide tower", pg[0] - 5, pg[1] - 1, 0.05, pg[0] - 3, pg[1] + 1, 2.2, (240, 196, 40), "SmoothPlastic")
ramp(park, "Slide", pg[0] - 0.5, pg[1], 0.05, 5.0, 0.9, 2.15, math.pi, (60, 160, 220), "SmoothPlastic")
for x in (pg[0] + 3.0, pg[0] + 6.0):
    aabb(park, "Swing frame", x - 0.08, pg[1] - 2.0, 0.05, x + 0.08, pg[1] - 1.84, 2.6, (200, 60, 60), "Metal")
    aabb(park, "Swing frame", x - 0.08, pg[1] + 1.84, 0.05, x + 0.08, pg[1] + 2.0, 2.6, (200, 60, 60), "Metal")
aabb(park, "Swing bar", pg[0] + 2.9, pg[1] - 2.0, 2.6, pg[0] + 6.1, pg[1] + 2.0, 2.76, (200, 60, 60), "Metal")
for y in (pg[1] - 0.9, pg[1] + 0.9):
    st = ybox(park, "Swing", pg[0] + 4.5, y, 0.55, 0.5, 0.45, 0.06, math.pi / 2, (40, 40, 44), "SmoothPlastic", cls="Seat")
    st.props["Disabled"] = ("bool", False)
for k in range(30):
    for _ in range(40):
        q = np.array([rnd.uniform(PX0 + SW + 2, PX1 - SW - 2), rnd.uniform(PY0 + SW + 2, PY1 - SW - 2)])
        if lx0 - 10 < q[0] < lx1 + 10 and ly0 - 10 < q[1] < ly1 + 10:
            continue
        if any(r[0] - 2.5 < q[0] < r[2] + 2.5 and r[1] - 2.5 < q[1] < r[3] + 2.5 for r in PATHS_PARK):
            continue
        if math.hypot(*(q - gz)) < 9 or math.hypot(*(q - pg)) < 11 or DLO - 4 < dk(q) < DHI + 4:
            continue
        tree(park, q, 7 + rnd.random() * 5, 2.8 + rnd.random() * 1.6, SPECIES[rnd.choice([0, 1, 0, 1, 2, 3])])
        break
for q in ((loop_[0] + 1.5, loop_[1] + 1.5), (loop_[2] - 1.5, loop_[1] + 1.5), (loop_[0] + 1.5, loop_[3] - 1.5),
          (loop_[2] - 1.5, loop_[3] - 1.5), (118.0, -18.0), (118.0, 75.0)):
    lp = new(city_lamps, "Model", "Park light")
    vcyl(lp, "Pole", q[0] + 1.6, q[1], 0.06, 3.6, 0.14, (40, 44, 48), "Metal")
    head = ball(lp, "Head", q[0] + 1.6, q[1], 3.9, 0.6, (255, 236, 200), collide=False)
    light(head, rng=24, brightness=1.4, color=(255, 220, 170), enabled=False, name="NightLight")
for q in ((118.0, 31.0, 1.0), (100.0, -4.0, 1.4), (136.0, -4.0, 3.2), (loop_[0] + 1.5, 43.0, 1.0),
          (loop_[2] - 1.5, 43.0, 1.0), (118.0, loop_[3] - 1.5, 1.0), (106.0, loop_[1] + 1.5, 1.0),
          (130.0, loop_[1] + 1.5, 1.0)):
    coin(*q)

# ---- VAYU, the hotel from the VAYU project, on the block north of the mall
VAYU = json.loads((ROOT / "data" / "vayu_model.json").read_text())
VX, VY = -5.0, 94.0                                 # site origin in city metres
vayu = new(city, "Model", "VAYU Hotel")
vayu_doors = new(vayu, "Folder", "Doors")
VLEV = {l["name"]: l["elev"] for l in VAYU["levels"]}
VMAT = {
    "concrete": ((226, 222, 214), "Concrete", {}), "masonry": ((178, 104, 76), "Brick", {}),
    "glass": (GLASS, "Glass", dict(tr=0.55, refl=0.05, shadow=False)), "steel": ((84, 90, 96), "Metal", {}),
    "canopy": ((240, 238, 230), "Fabric", {}), "aluminium": ((196, 200, 204), "Metal", {}),
    "planting": ((86, 128, 58), "Grass", {}), "terracotta": ((196, 108, 72), "Brick", {}),
    "pv": ((28, 38, 66), "Glass", dict(refl=0.25)), "pv_glass": ((60, 80, 110), "Glass", dict(tr=0.3, refl=0.2)),
    "water": ((60, 160, 200), "Glass", dict(tr=0.3, refl=0.3, collide=False)),
    "green_roof": ((92, 132, 60), "Grass", {}), "stone": ((206, 198, 184), "Slate", {}),
    "timber": ((150, 104, 66), "WoodPlanks", {}),
}
VDOORS = {"VH-0139": 75.8, "VH-1451": 80.0, "VH-1452": 80.0}       # curtain walls given a door, at site x


def vrect(pts):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs) + VX, min(ys) + VY, max(xs) + VX, max(ys) + VY


def is_rect(pts):
    return len(pts) == 4 and len({round(p[0], 4) for p in pts}) == 2 and len({round(p[1], 4) for p in pts}) == 2


v_levels = {}
for e in VAYU["elements"]:
    if e["level"] == "B1" or e["kind"] == "tree":
        continue
    if e["level"] not in v_levels:
        v_levels[e["level"]] = new(vayu, "Folder", e["level"])
    lv, zl = v_levels[e["level"]], VLEV[e["level"]]
    color, mat, kw = VMAT[e["material"]]
    loops = e.get("loops") or []
    if e["kind"] == "slab" and len(loops) > 1:
        top, t = zl + e["top"], e["solids"][0]["h"]
        if len(loops) == 2 and all(is_rect(l) for l in loops):
            x0, y0, x1, y1 = vrect(loops[0])
            hx0, hy0, hx1, hy1 = vrect(loops[1])
            for r in ((x0, y0, x1, hy0), (x0, hy1, x1, y1), (x0, hy0, hx0, hy1), (hx1, hy0, x1, hy1)):
                if r[2] - r[0] > 0.01 and r[3] - r[1] > 0.01:
                    aabb(lv, e["name"], r[0], r[1], top - t, r[2], r[3], top, color, mat, **kw)
        else:
            sh = lambda loop: ccw([np.array([p[0] + VX, p[1] + VY]) for p in loop])
            slab(lv, e["name"], sh(loops[0]), [sh(l) for l in loops[1:]], top, t, color, mat, **kw)
        continue
    for s in e["solids"]:
        if s["type"] == "x":          # sloped roof teeth: a section in (y, z) run along x
            xc = s["x0"] + s["len"] / 2 + VX
            q = [R3(xc, p[0] + VY, p[1] + zl) for p in s["pts"]]
            for i in range(1, len(q) - 1):
                for centre, R, size in tri_wedges(q[0], q[i], q[i + 1], s["len"] * K):
                    part(lv, e["name"], centre, R, size, color, mat, cls="WedgePart", **kw)
            continue
        x0, y0, x1, y1 = vrect(s["pts"])
        z0, z1 = zl + s["z0"], zl + s["z0"] + s["h"]
        if e["id"] in VDOORS:
            dx, yc = VDOORS[e["id"]] + VX, (y0 + y1) / 2
            aabb(lv, e["name"], x0, y0, z0, dx - 2.0, y1, z1, color, mat, **kw)
            aabb(lv, e["name"], dx + 2.0, y0, z0, x1, y1, z1, color, mat, **kw)
            aabb(lv, e["name"], dx - 2.0, y0, z0 + 2.9, dx + 2.0, y1, z1, color, mat, **kw)
            aabb(lv, "Door head", dx - 2.0, yc - 0.11, z0 + 2.75, dx + 2.0, yc + 0.11, z0 + 2.9, MULL, "Metal")
            auto_door(vayu_doors, np.array([dx - 2.0, yc]), np.array([dx + 2.0, yc]), z0, out=0.0)
            continue
        aabb(lv, e["name"], x0, y0, z0, x1, y1, z1, color, mat, **kw)

VTREE = {"Rain tree": [(84, 120, 52), (98, 134, 60), (76, 110, 46)],
         "Pink tabebuia": [(228, 141, 179), (240, 166, 197), (214, 120, 160)],
         "Gulmohar": [(216, 71, 29), (232, 93, 36), (200, 60, 30)], "Neem": [(90, 128, 54), (104, 140, 62), (80, 116, 48)],
         "Frangipani": [(240, 236, 220), (250, 230, 200), (110, 140, 70)],
         "Atrium ficus": [(70, 110, 50), (84, 124, 58), (64, 100, 46)]}
v_trees = new(vayu, "Folder", "Trees")
for t_ in VAYU["trees"]:
    tree(v_trees, np.array([t_["x"] + VX, t_["y"] + VY]), t_["h"], t_["r"], VTREE[t_["species"]], n=5, z0=0.0)
v_land = new(vayu, "Folder", "Landscape")
shift = lambda loop: [np.array([p[0] + VX, p[1] + VY]) for p in loop]
land = VAYU["landscape"]
slab(v_land, "Drive", ccw(shift(land["drive"])), [], 0.05, 0.2, (92, 94, 98), "Asphalt")
for nm, loop in [("Plaza", land["plaza"]), ("Service yard", land["service_yard"]), ("Ramp", land["ramp"])] + \
        [("Path", p_) for p_ in land["paths"]]:
    x0, y0, x1, y1 = vrect(loop)
    aabb(v_land, nm, x0, y0, -0.12, x1, y1, 0.04, (206, 198, 184), "Slate")
vsign = wall(v_land, "VAYU sign", np.array([57.5, 104.0]), np.array([67.5, 104.0]), 0.05, 2.6, 0.6, (40, 40, 44), "Slate")
sign(vsign, "VAYU", face="Back")
car_pad(91.0, 104.0, 0.04, 83.5, 104.0, -math.pi / 2)
parked(55.0, 119.0, 0.05, 0.0)
parked(70.0, 119.0, 0.05, 0.0)
VSKY = VLEV["ROOF"] + 1.0
portal("VAYU lobby", 57.2, 135.0, 0.04, "VAYU sky deck", "Up to the sky pool")
portal("VAYU sky deck", 66.2, 134.0, VSKY, "VAYU lobby", "Down to the lobby")
for q in ((70.8, 136.0, 1.0), (75.0, 147.0, 1.0), (82.2, 137.0, VSKY + 1.0), (95.0, 137.0, VSKY + 1.0),
          (25.0, 186.0, 1.0)):
    coin(*q)

# ---- stunt park: mega ramp, jumps, quarter pipe, slalom, drift circle and a fuel station
stunt = new(city, "Folder", "StuntPark")
SX0, SY0, SX1, SY1 = BLOCKS["C56R4"]
paved(stunt, "Stunt pad", SX0 + SW, SY0 + SW, SX1 - SW, SY1 - SW, 0.1, 0.25, (54, 56, 60), "Asphalt")
car_pad(218.0, 99.0, 0.1, 228.0, 100.0, 0.0)
ramp(stunt, "Mega ramp", 252.5, 206.0, 0.1, 75.0, 12.0, 15.9, 0.0, (250, 190, 40), "DiamondPlate")
aabb(stunt, "Mega ramp deck", 290.0, 196.0, 15.4, 306.0, 216.0, 16.0, (220, 222, 224), "DiamondPlate")
for x, y in ((291, 197), (305, 197), (291, 215), (305, 215)):
    aabb(stunt, "Deck leg", x - 0.6, y - 0.6, 0.1, x + 0.6, y + 0.6, 15.4, (90, 96, 102), "Metal")
aabb(stunt, "Deck rail", 290.0, 215.7, 16.0, 306.0, 216.0, 17.1, (240, 90, 40), "Metal")
aabb(stunt, "Deck rail", 305.7, 196.0, 16.0, 306.0, 215.7, 17.1, (240, 90, 40), "Metal")
ramp(stunt, "Drop ramp", 298.0, 166.0, 0.1, 60.0, 12.0, 15.9, math.pi / 2, (240, 100, 40), "DiamondPlate")
banner = aabb(stunt, "Mega ramp banner", 290.0, 215.2, 17.1, 306.0, 215.6, 20.5, (18, 26, 60), "Neon")
sign(banner, "MEGA RAMP", face="Back", style="led", accent=(255, 120, 40))
ramp(stunt, "Kicker", 226.0, 150.0, 0.1, 10.0, 10.0, 3.6, 0.0, (60, 200, 255), "DiamondPlate")
ramp(stunt, "Landing", 244.0, 150.0, 0.1, 14.0, 12.0, 3.6, math.pi, (60, 200, 255), "DiamondPlate")
ramp(stunt, "Big kicker", 260.0, 124.0, 0.1, 12.0, 10.0, 5.0, 0.0, (230, 60, 120), "DiamondPlate")
ramp(stunt, "Big landing", 283.5, 124.0, 0.1, 17.0, 12.0, 5.0, math.pi, (230, 60, 120), "DiamondPlate")
ramp(stunt, "Quarter pipe", 175.0, 170.0, 0.1, 6.0, 40.0, 5.0, math.pi, (200, 204, 210), "Concrete")
for i, x in enumerate(np.arange(232.0, 300.0, 7.0)):
    cone = vcyl(stunt, "Cone", x, 108.0 + (1.6 if i % 2 else -1.6), 0.1, 0.75, 0.42, (255, 110, 20), "SmoothPlastic")
    cone.props["Anchored"] = ("bool", False)
for k in range(18):
    ang = k * 2 * math.pi / 18
    q = np.array([200.0, 172.0]) + 13 * np.array([math.cos(ang), math.sin(ang)])
    ybox(stunt, "Drift ring", q[0], q[1], 0.1, 4.0, 0.3, 0.012, ang + math.pi / 2, MARK, collide=False, query=False,
         shadow=False)
for q in ((174.0, 98.0), (315.0, 98.0), (174.0, 220.0), (315.0, 160.0)):
    lp = new(city_lamps, "Model", "Floodlight")
    vcyl(lp, "Mast", q[0], q[1], 0.1, 16.0, 0.4, (150, 154, 158), "Metal")
    head = aabb(lp, "Head", q[0] - 1.2, q[1] - 1.2, 16.0, q[0] + 1.2, q[1] + 1.2, 16.8, (255, 236, 200))
    light(head, rng=60, brightness=2.6, color=(255, 236, 210), enabled=False, name="NightLight")
for x0 in (180.0, 222.0):                     # bleachers along the north edge
    for k in range(3):
        aabb(stunt, "Bleacher", x0, 218.0 + k * 1.2, 0.1, x0 + 34, 223.0, 0.6 + k * 0.5, (150, 156, 162), "Metal")
portal("Stunt park floor", 282.0, 188.0, 0.1, "Mega ramp top", "Up to the mega ramp")
portal("Mega ramp top", 298.0, 206.0, 16.0, "Stunt park floor", "Down to the floor")
gas = new(stunt, "Model", "Fuel station")
canopy = aabb(gas, "Canopy", 180.0, 100.0, 5.2, 206.0, 114.0, 6.0, (244, 244, 240), "SmoothPlastic")
sign(canopy, "GLASSTOP FUEL", face="Back")
aabb(gas, "Canopy light", 180.3, 100.3, 5.1, 205.7, 113.7, 5.2, (255, 250, 236), "Neon", collide=False)
for x, y in ((182.0, 102.0), (204.0, 102.0), (182.0, 112.0), (204.0, 112.0)):
    vcyl(gas, "Canopy column", x, y, 0.1, 5.1, 0.5, (200, 40, 40), "Metal")
for y in (104.5, 109.5):
    aabb(gas, "Pump island", 185.0, y - 0.6, 0.1, 201.0, y + 0.6, 0.3, (200, 200, 196), "Concrete")
    for x in (189.0, 197.0):
        aabb(gas, "Pump", x - 0.5, y - 0.3, 0.3, x + 0.5, y + 0.3, 2.0, (230, 230, 226), "SmoothPlastic")
        aabb(gas, "Pump stripe", x - 0.52, y - 0.32, 1.5, x + 0.52, y + 0.32, 1.7, (60, 220, 255), "Neon", collide=False)
mart = aabb(gas, "Fuel mart", 176.0, 117.0, 0.1, 200.0, 125.5, 4.2, (236, 232, 224), "Concrete")
aabb(gas, "Mart glass", 178.0, 116.94, 0.4, 198.0, 117.0, 3.2, (60, 90, 110), "Glass", refl=0.2)
mart_sign = aabb(gas, "Mart sign", 182.0, 116.7, 3.3, 194.0, 116.9, 4.0, (200, 40, 40))
sign(mart_sign, "MART  ·  24/7", face="Back")
aabb(gas, "Price sign post", 209.6, 97.6, 0.1, 210.4, 98.4, 5.0, (70, 74, 78), "Metal")
price = aabb(gas, "Price sign", 208.0, 97.8, 5.0, 212.0, 98.2, 7.4, (18, 26, 60), "Neon")
sign(price, "FUEL", face="Back", style="led", accent=(255, 70, 40))
parked(186.0, 107.0, 0.1, 0.0)
parked(214.0, 120.0, 0.1, math.pi / 2)
for q in ((233.5, 150.0, 5.6), (236.5, 150.0, 5.2), (268.5, 124.0, 7.6), (271.5, 124.0, 7.6), (252.5, 206.0, 9.5),
          (298.0, 206.0, 17.2), (298.0, 166.0, 9.5), (173.5, 170.0, 4.6), (200.0, 172.0, 1.0), (250.0, 108.0, 1.0),
          (285.0, 108.0, 1.0), (310.0, 125.0, 1.0)):
    coin(*q)

# ---- Glass Bay: promenade, palms, beach umbrellas, lifeguard tower and a pier
beach = new(city, "Folder", "Beach")
for x0, y0, x1, y1 in tiles(339.5, -300.0, 348.0, 360.0):
    aabb(beach, "Promenade", x0, y0, -0.3, x1, y1, 0.12, (168, 122, 80), "WoodPlanks")
car_pad(344.5, -4.0, 0.12, 343.8, -14.0, -math.pi / 2)
for y in np.arange(-280.0, 345.0, 24.0):
    x = 351.5 + rnd.uniform(-1, 1)
    h = rnd.uniform(7, 9.5)
    pm = new(beach, "Model", "Palm")
    vcyl(pm, "Trunk", x, y, -0.4, h, 0.4, (140, 108, 74), "Wood")
    for k in range(6):
        ang = k * math.pi / 3 + rnd.uniform(-0.2, 0.2)
        u = np.array([math.cos(ang) * math.cos(0.35), math.sin(ang) * math.cos(0.35), -math.sin(0.35)])
        side = np.array([-math.sin(ang), math.cos(ang), 0.0])
        n = np.cross(u, side)
        if n[2] < 0:
            side, n = -side, -n
        c = np.array([x, y, h - 0.4]) + u * 2.4
        mbox(pm, "Frond", tuple(c), (tuple(u), tuple(n), tuple(np.cross(u, n))), (4.8, 0.08, 1.2), (70, 140, 60), "Grass",
             collide=False)
    ball(pm, "Coconuts", x, y, h - 0.6, 0.8, (110, 80, 40), "Wood", collide=False)
UMB = [(230, 70, 60), (250, 200, 40), (60, 150, 220), (240, 240, 236), (60, 180, 120)]
for k, (x, y) in enumerate(((362, -60), (370, -30), (360, 0), (374, 45), (364, 70), (372, 100), (360, 130),
                            (368, -95), (376, 160), (362, 190))):
    vcyl(beach, "Umbrella pole", x, y, -0.2, 2.6, 0.08, (230, 230, 226), "Metal")
    vcyl(beach, "Umbrella", x, y, 2.3, 0.25, 3.0, UMB[k % len(UMB)], "Fabric", collide=False)
    ybox(beach, "Towel", x + 1.6, y, -0.18, 0.9, 1.8, 0.03, 0.3 * k, UMB[(k + 2) % len(UMB)], "Fabric", collide=False)
lg = (380.0, 15.0)
for dx_ in (-1.0, 1.0):
    for dy_ in (-1.0, 1.0):
        aabb(beach, "Lifeguard leg", lg[0] + dx_ - 0.1, lg[1] + dy_ - 0.1, -0.3, lg[0] + dx_ + 0.1, lg[1] + dy_ + 0.1, 3.0,
             WHITE, "Wood")
aabb(beach, "Lifeguard deck", lg[0] - 1.4, lg[1] - 1.4, 3.0, lg[0] + 1.4, lg[1] + 1.4, 3.15, WHITE, "WoodPlanks")
aabb(beach, "Lifeguard hut", lg[0] - 1.0, lg[1] - 1.0, 3.15, lg[0] + 1.0, lg[1] + 1.0, 5.0, (230, 60, 50), "Wood")
ramp(beach, "Lifeguard ladder", lg[0] - 3.0, lg[1], -0.3, 3.2, 0.9, 3.3, 0.0, WHITE, "WoodPlanks")
PIER_Z = 1.6
ramp(beach, "Pier ramp", 353.0, 31.0, 0.12, 10.0, 6.0, PIER_Z - 0.12, 0.0, (150, 104, 66), "WoodPlanks")
aabb(beach, "Pier", 358.0, 28.0, PIER_Z - 0.3, 440.0, 34.0, PIER_Z, (150, 104, 66), "WoodPlanks")
for x in np.arange(362.0, 441.0, 8.0):
    for y in (28.3, 33.7):
        vcyl(beach, "Pier post", x, y, -6.0, 6.0 + PIER_Z + 1.0, 0.35, (110, 80, 54), "Wood")   # also the rail posts
for y0 in (28.0, 33.88):
    aabb(beach, "Pier rail", 358.0, y0, PIER_Z + 0.9, 440.0, y0 + 0.12, PIER_Z + 1.0, WHITE, "Wood")
aabb(beach, "Pavilion roof", 428.0, 27.0, PIER_Z + 3.2, 440.0, 35.0, PIER_Z + 3.5, (200, 70, 60), "Wood")
for x, y in ((428.5, 28.2), (439.5, 28.2), (428.5, 33.8), (439.5, 33.8)):
    aabb(beach, "Pavilion post", x - 0.12, y - 0.12, PIER_Z, x + 0.12, y + 0.12, PIER_Z + 3.2, WHITE, "Wood")
bay_sign = wall(beach, "Bay sign", np.array([344.5, 36.0]), np.array([344.5, 26.0]), 0.12, 2.0, 0.4, (30, 40, 60))
sign(bay_sign, "GLASS BAY", face="Back")
parked(343.8, -40.0, 0.12, -math.pi / 2)
parked(343.8, 60.0, 0.12, math.pi / 2)
for q in ((380.0, 15.0, 6.0), (436.0, 31.0, PIER_Z + 1.0), (400.0, 31.0, PIER_Z + 1.0), (344.0, 120.0, 1.1),
          (344.0, -120.0, 1.1), (365.0, 100.0, 0.7), (365.0, -60.0, 0.7)):
    coin(*q)

# ---- coins round the ring and down the avenues, parked cars at the kerbs
for k, s in enumerate(np.arange(30.0, 2 * (RE - RW + RN - RS), 70.0)):
    o = -4.0 if k % 2 else 4.0
    L1, L2, L3 = RE - RW, RN - RS, 2 * (RE - RW) + (RN - RS)
    if s < L1:
        q = (RW + s, RS + o)
    elif s < L1 + L2:
        q = (RE + o, RS + s - L1)
    elif s < L3:
        q = (RE - (s - L1 - L2), RN + o)
    else:
        q = (RW + o, RN - (s - L3))
    if not on_blvd(q, 2.0):
        coin(q[0], q[1], 1.0)
for (ax, top), own in zip(AVENUES, AVE):
    for y in np.arange(own[1] + 50, own[3] - 20, 110):
        if not on_road((ax, y), own, 2.0) and not on_blvd((ax, y), 2.0):
            coin(ax + 1.8, y, 1.0)
for x, y, h_ in ((-18.3, 120.0, math.pi / 2), (-9.1, 150.0, -math.pi / 2), (-18.3, -40.0, math.pi / 2),
                 (157.7, 20.0, math.pi / 2), (166.9, -30.0, -math.pi / 2), (166.9, 130.0, -math.pi / 2),
                 (69.7, -140.0, math.pi / 2), (78.9, -205.0, -math.pi / 2), (60.0, 236.6, 0.0), (120.0, 227.4, math.pi)):
    own = [r for r in ROAD_RECTS if r[0] <= x <= r[2] and r[1] <= y <= r[3]]
    if own and not on_blvd((x, y), 3.0) and not on_road((x, y), own[0], 3.0):
        parked(x, y, 0.0, h_)
coin(29.4, 22.0, 1.0)
coin(18.0, 30.0, 1.0)
coin(*(P(900, 862) + np.array([0.0, 0.6])), z4 + 1.0)

# ---- AI traffic: the ring, the boulevard, two avenues and a street (cars keep left)
def rounded_rect(x0, y0, x1, y1, r, n=4):
    pts = []
    for (cx, cy), a0 in (((x1 - r, y0 + r), -math.pi / 2), ((x1 - r, y1 - r), 0.0), ((x0 + r, y1 - r), math.pi / 2),
                         ((x0 + r, y0 + r), math.pi)):
        for i in range(n + 1):
            a = a0 + math.pi / 2 * i / n
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


TRAFFIC = [
    (rounded_rect(RW, RS, RE, RN, 14.0), True, ((-2.4, 1), (-6.6, 1), (2.4, -1), (6.6, -1)), 12, 66.0),
    ([diagA + dDir * t0 + dOut * 15.25, diagA + dDir * t1 + dOut * 15.25], False,
     ((-7.05, 1), (-3.65, 1), (3.35, -1), (6.75, -1)), 6, 46.0),
    ([(162.3, RS), (162.3, RN)], False, ((-1.8, 1), (1.8, -1)), 4, 38.0),
    ([(-13.7, RS), (-13.7, RN)], False, ((-1.8, 1), (1.8, -1)), 4, 38.0),
    ([(RW, 86.0), (RE, 86.0)], False, ((-1.8, 1), (1.8, -1)), 4, 38.0),
]
for k in range(sum(t[3] for t in TRAFFIC)):
    q = np.array([-60.0 + (k % 10) * 4, -200.0 - (k // 10) * 7])
    cm = new(traffic_f, "Model", "Car", ModelStreamingMode=("token", 1))
    colour = rnd.choice([(232, 232, 230), (40, 44, 50), (140, 146, 150), (183, 59, 47), (31, 59, 92), (220, 218, 212),
                         (250, 196, 40), (40, 120, 80)])
    body = aabb(cm, "Body", q[0] - 0.9, q[1] - 2.15, 0.25, q[0] + 0.9, q[1] + 2.15, 1.05, colour, "SmoothPlastic",
                collide=False, refl=0.1)
    cm.props["PrimaryPart"] = ("ref", body)
    aabb(cm, "Cabin", q[0] - 0.8, q[1] - 1.1, 1.05, q[0] + 0.8, q[1] + 1.0, 1.6, (30, 36, 44), "Glass", collide=False, refl=0.2)
    aabb(cm, "Headlights", q[0] - 0.75, q[1] + 2.15, 0.6, q[0] + 0.75, q[1] + 2.2, 0.8, (255, 246, 220), "Neon", collide=False)
    aabb(cm, "Taillights", q[0] - 0.75, q[1] - 2.2, 0.6, q[0] + 0.75, q[1] - 2.15, 0.8, (220, 40, 30), "Neon", collide=False)
    for wx in (-0.78, 0.78):
        for wy in (-1.35, 1.35):
            mbox(cm, "Wheel", (q[0] + wx, q[1] + wy, 0.33), UP, (0.26, 0.66, 0.66), (26, 26, 28), shape=2, collide=False)

spawn_c = P(1000, 860)
sp_ = aabb(ws, "SpawnLocation", spawn_c[0] - 1.8, spawn_c[1] - 1.8, -0.05, spawn_c[0] + 1.8, spawn_c[1] + 1.8, 0.05,
           PAVE, "Slate", cls="SpawnLocation")
sp_.props.update(Neutral=("bool", True), Duration=("int", 0), Enabled=("bool", True))

# ---- what the scripts are told about the city
PLACES = [("Glass Mall", (29.4, 25.4, 0.1)), ("Mall car park", (-1.5, -71.3, 0.1)),        # beside car pads and portals
          ("VAYU Hotel lobby", (59.7, 135.0, 0.05)), ("VAYU sky pool", (82.2, 137.5, VSKY)),
          ("Downtown plaza", (185.5, 50.0, 0.13)), ("Central Park", (118.0, 70.5, 0.06)),
          ("Stunt park", (219.5, 101.5, 0.1)), ("Mega ramp top", (298.0, 200.0, 16.0)),
          ("Glass Bay beach", (344.5, -1.3, 0.12)), ("Pier", (420.0, 31.0, PIER_Z)),
          ("Suburbs", (-35.0, 158.0, 0.0)), ("Midtown", (85.3, -100.3, 0.1)), ("Uptown", (67.3, 243.0, 0.1))]
if SPIRE:                                           # in front of the Glass Spire's doors
    sx, sy, sd, sf_ = SPIRE
    door_ = np.array([sx, sy]) + np.array(sf_) * (sd / 2 + 4 + 3.0)
    PLACES.insert(5, ("Glass Spire", (door_[0], door_[1], 0.15)))


def srect(x0, y0, x1, y1):
    a, b = R3(x0, y0, 0), R3(x1, y1, 0)
    return min(a[0], b[0]), min(a[2], b[2]), max(a[0], b[0]), max(a[2], b[2])


B = BLOCKS
DISTRICTS = [("Glass Mall car park", LOT), ("Glass Mall", B["C3R3"]), ("VAYU Hotel", B["C34R4"]),
             ("Central Park", B["C4R3"]), ("Stunt Park", B["C56R4"]), ("Downtown", (B["C5R1"][0], B["C5R1"][1], B["C6R3"][2], B["C6R3"][3])),
             ("Midtown", (B["C3R1"][0], B["C3R1"][1], B["C4R2"][2], B["C4R2"][3])),
             ("Uptown", (B["C34R5"][0], B["C34R5"][1], B["C56R5"][2], B["C56R5"][3])),
             ("Suburbs", (B["C1R1"][0], B["C1R1"][1], B["C2R5"][2], B["C2R5"][3]))] + \
            [("Ring Highway", r) for r in RING] + \
            [("City streets", (RW - RH, RS - RH, RE + RH, RN + RH)), ("Glass Bay", (RE + RH, -600.0, 1400.0, 700.0))]


def terrain_box(x0, y0, z0, x1, y1, z1):
    a, b = R3(x0, y0, z0), R3(x1, y1, z1)
    return "{ %s }" % ", ".join(num(v) for v in list((a + b) / 2) + list(np.abs(b - a)))


hills = []
for y in np.arange(-500.0, 600.0, 80.0):
    hills.append((rnd.uniform(-460, -350), y, rnd.uniform(36, 60)))
for x in np.arange(-420.0, 340.0, 80.0):
    hills.append((x, rnd.uniform(450, 570), rnd.uniform(36, 60)))
    hills.append((x, rnd.uniform(-520, -400), rnd.uniform(36, 60)))
TERRAIN = "{\n\twater = { %s },\n\tsand = { %s, %s },\n\twedges = { %s },\n\tlakeBed = %s,\n\tlake = %s,\n" \
          "\thills = { %s },\n\trocks = { %s },\n}" % (
              terrain_box(400, -540, -5.0, 1000, 600, -0.6),
              terrain_box(348, -540, -6.0, 400, 600, -0.15), terrain_box(400, -540, -9.0, 1000, 600, -5.0),
              terrain_box(400, -540, -5.0, 450, 600, -0.15),
              terrain_box(lx0, ly0, -4.0, lx1, ly1, -3.4), terrain_box(lx0, ly0, -3.4, lx1, ly1, -0.4),
              ", ".join("{ %s }" % ", ".join(num(v) for v in list(R3(x, y, -r * 0.55)) + [r * K]) for x, y, r in hills),
              ", ".join("{ %s }" % ", ".join(num(v) for v in list(R3(x, y, z)) + [r * K]) for x, y, z, r in
                        ((420, 160, -1.0, 5), (446, -210, -1.5, 7), (395, -320, -0.5, 6), (470, 260, -2.0, 9))))


# ------------------------------------------------------------------ lighting
lighting = Inst("Lighting", "Lighting",
                Ambient=("c3", (72, 72, 82)), OutdoorAmbient=("c3", (128, 128, 136)), Brightness=("float", 3),
                TimeOfDay=("string", "16:40:00"), GeographicLatitude=("float", 13),
                EnvironmentDiffuseScale=("float", 1), EnvironmentSpecularScale=("float", 1),
                GlobalShadows=("bool", True), ShadowSoftness=("float", 0.2), Technology=("token", 4),
                ExposureCompensation=("float", 0))
game_items.append(lighting)
new(lighting, "Atmosphere", "Atmosphere", Density=("float", 0.3), Offset=("float", 0.25), Color=("c3", (199, 184, 170)),
    Decay=("c3", (106, 112, 125)), Glare=("float", 0.3), Haze=("float", 1.2))
new(lighting, "Sky", "Sky", SunAngularSize=("float", 14), MoonAngularSize=("float", 11), StarCount=("int", 3000),
    CelestialBodiesShown=("bool", True))
new(lighting, "BloomEffect", "Bloom", Intensity=("float", 0.5), Size=("float", 24), Threshold=("float", 1.5))
new(lighting, "SunRaysEffect", "SunRays", Intensity=("float", 0.04), Spread=("float", 0.5))
new(lighting, "ColorCorrectionEffect", "Grade", Brightness=("float", 0), Contrast=("float", 0.06),
    Saturation=("float", 0.08), TintColor=("c3", (255, 250, 244)))


# ------------------------------------------------------------------ scripts
def lua_vec(v):
    return "Vector3.new(%s, %s, %s)" % tuple(num(float(c)) for c in v)


def lua_list(items):
    return "{\n%s\n}" % ",\n".join("\t" + i for i in items)


def xz(p):
    q = R3(p[0], p[1], 0)
    return "{ %s, %s }" % (num(q[0]), num(q[2]))


BLVD_A = R3(diagA[0], diagA[1], 0)
fill = {
    "__CAR_Y__": num(0.65 * K),
    "__CAR_FORWARD__": "-1",
    "__CAR_STEER__": "-1",
    "__FLOORS__": lua_list('{ y = %s, name = "%s", note = "%s" }' % (num(floor_top(i) * K), l[0], l[4])
                           for i, l in enumerate(LEVELS)),
    "__FOOTPRINTS__": lua_list("{ %s }" % ", ".join(xz(p) for p in POLY[l[3]]) for l in LEVELS),
    "__TERRACE__": "{ %s }" % ", ".join(xz(p) for p in tri),
    "__PATHS__": lua_list("{ pts = { %s }, loop = %s, lanes = { %s }, count = %d, speed = %s }" % (
        ", ".join(lua_vec(R3(p[0], p[1], 0.0)) for p in pts), "true" if loop else "false",
        ", ".join("{ %s, %d }" % (num(o * K), d) for o, d in lanes), count, num(speed))
        for pts, loop, lanes, count, speed in TRAFFIC),
    "__PLACES__": lua_list('["%s"] = %s' % (n, lua_vec(R3(*q))) for n, q in PLACES),
    "__PLACE_NAMES__": "{ %s }" % ", ".join('"%s"' % n for n, q in PLACES),
    "__BUILDINGS__": lua_list('{ name = "%s", rect = { %s }, floors = { %s } }' % (
        n, ", ".join(num(v) for v in srect(*r)), ", ".join('{ %s, "%s" }' % (num(z * K), t) for z, t in fl))
        for n, r, fl in BUILDINGS),
    "__DISTRICTS__": lua_list('{ "%s", %s }' % (n, ", ".join(num(v) for v in srect(*r))) for n, r in DISTRICTS),
    "__BLVD__": "{ a = %s, dir = %s, out = %s, lo = %s, hi = %s, t0 = %s, t1 = %s }" % (
        lua_vec(BLVD_A), lua_vec(D3(dDir[0], dDir[1], 0)), lua_vec(D3(dOut[0], dOut[1], 0)), num(5.5 * K), num(25 * K),
        num(t0 * K), num(t1 * K)),
    "__TERRAIN__": TERRAIN,
}


def script_src(fname):
    src = (SCRIPTS / fname).read_text()
    for k, v in fill.items():
        src = src.replace(k, v)
    assert "__" not in src.replace("__index", "").replace("__mode", ""), fname
    return src


sss = Inst("ServerScriptService", "ServerScriptService")
game_items.append(sss)
for f in sorted(SCRIPTS.glob("*.server.lua")):
    new(sss, "Script", f.name.split(".")[0], Source=("src", script_src(f.name)))
rs = Inst("ReplicatedStorage", "ReplicatedStorage")
game_items.append(rs)
new(rs, "RemoteEvent", "Travel")
for f in sorted(SCRIPTS.glob("*.module.lua")):
    new(rs, "ModuleScript", f.name.split(".")[0], Source=("src", script_src(f.name)))
sp = Inst("StarterPlayer", "StarterPlayer")
game_items.append(sp)
sps = new(sp, "StarterPlayerScripts", "StarterPlayerScripts")
for f in sorted(SCRIPTS.glob("*.client.lua")):
    new(sps, "LocalScript", f.name.split(".")[0], Source=("src", script_src(f.name)))

out = ['<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
       'xsi:noNamespaceSchemaLocation="http://www.roblox.com/roblox.xsd" version="4">',
       "<External>null</External>", "<External>nil</External>"]
for item in game_items:
    write_item(item, out)
out.append("</roblox>")
OUT.write_text("\n".join(out))
if __name__ == "__main__":
    print("wrote %s: %d parts, %d KB" % (OUT.name, len(PARTS), OUT.stat().st_size // 1024))
