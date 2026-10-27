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

# ---- lift: shaft, landing doors, call buttons, car
x0, y0, x1, y1 = SHAFT
xc = (x0 + x1) / 2
shaft = new(lift_f, "Folder", "Shaft")
landings = new(lift_f, "Folder", "Landings")
TOP = ROOF_Z + 2.0
aabb(shaft, "Shaft wall", x0, y0, 0.03, x0 + 0.25, y1, TOP, CORE, "Concrete")
aabb(shaft, "Shaft wall", x1 - 0.25, y0, 0.03, x1, y1, TOP, CORE, "Concrete")
aabb(shaft, "Shaft wall", x0, y1 - 0.25, 0.03, x1, y1, TOP, CORE, "Concrete")
aabb(shaft, "Shaft roof", x0, y0, TOP, x1, y1, TOP + 0.25, CORE, "Concrete")
for i in range(5):
    zf = floor_top(i)
    znext = floor_top(i + 1) if i < 4 else ROOF_Z + 0.5
    aabb(shaft, "Shaft front", x0, y0, zf, xc - 0.9, y0 + 0.25, znext, CORE, "Concrete")
    aabb(shaft, "Shaft front", xc + 0.9, y0, zf, x1, y0 + 0.25, znext, CORE, "Concrete")
    aabb(shaft, "Shaft front", xc - 0.9, y0, zf + 2.5, xc + 0.9, y0 + 0.25, znext, CORE, "Concrete")
    door = new(landings, "Model", "Door%d" % (i + 1))
    for side, xa, xb in (("L", xc - 0.92, xc + 0.02), ("R", xc - 0.02, xc + 0.92)):
        aabb(door, side, xa, y0 - 0.07, zf, xb, y0 - 0.01, zf + 2.45, (200, 210, 214), "Metal", refl=0.2)
    values(door, Slide=0.9 * K)
    call = aabb(landings, "Call%d" % (i + 1), xc + 1.15, y0 - 0.06, zf + 1.0, xc + 1.45, y0, zf + 1.4, (30, 34, 40))
    sign(call, "CALL", style="button")
    new(call, "ClickDetector", "ClickDetector", MaxActivationDistance=("float", 14))
    new(call, "ProximityPrompt", "ProximityPrompt", ActionText=("string", "Call lift"), ObjectText=("string", "Lift"),
        HoldDuration=("float", 0), MaxActivationDistance=("float", 10), RequiresLineOfSight=("bool", False))
    directory = aabb(landings, "Directory", xc - 2.5, y0 - 0.06, zf + 0.9, xc - 1.2, y0, zf + 2.3, (20, 24, 28))
    sign(directory, "%s  ·  YOU ARE HERE\n\n4F  Cinemas · Terrace\n3F  Arcade · Games\n2F  Food court\n1F  Fashion\nGF  Shops · Exit"
         % LEVELS[i][0], style="directory")
car = new(lift_f, "Model", "Car")
cx0, cy0, cx1, cy1 = x0 + 0.4, y0 + 0.35, x1 - 0.4, y1 - 0.4
z = floor_top(0)
floor_part = aabb(car, "Floor", cx0, cy0, z - 0.2, cx1, cy1, z, (90, 96, 102), "Marble")
car.props["PrimaryPart"] = ("ref", floor_part)
aabb(car, "Back", cx0, cy1 - 0.08, z, cx1, cy1, z + 2.5, (200, 220, 226), "Glass", tr=0.3, refl=0.3)
aabb(car, "Side", cx0, cy0, z, cx0 + 0.08, cy1, z + 2.5, GLASS, "Glass", tr=0.5, shadow=False)
aabb(car, "Side", cx1 - 0.08, cy0, z, cx1, cy1, z + 2.5, GLASS, "Glass", tr=0.5, shadow=False)
aabb(car, "Roof", cx0, cy0, z + 2.5, cx1, cy1, z + 2.6, (230, 232, 234))
light(aabb(car, "Lamp", cx0 + 0.6, cy0 + 0.6, z + 2.46, cx1 - 0.6, cy1 - 0.6, z + 2.5, (255, 246, 230), "Neon",
           collide=False), rng=12)
for n in range(5):
    zb = z + 0.9 + n * 0.22
    btn = aabb(car, "Button%d" % (n + 1), cx1 - 0.14, cy0 + 1.0, zb, cx1 - 0.08, cy0 + 1.3, zb + 0.18, (30, 34, 40))
    sign(btn, LEVELS[n][0], face="Left", style="button")
    new(btn, "ClickDetector", "ClickDetector", MaxActivationDistance=("float", 14))

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


# ---- buildings
def midrise(parent, x0, y0, x1, y1, floors, color, glass, fh=3.6, z0=0.1, name="Building"):
    m = new(parent, "Model", name)
    top = z0 + floors * fh + 0.6
    aabb(m, "Walls", x0, y0, z0 - 0.2, x1, y1, top, color, "Concrete")
    for f in range(floors):
        za, zb = z0 + f * fh + (0.4 if f == 0 else 1.0), z0 + f * fh + (3.2 if f == 0 else 2.8)
        aabb(m, "Lit window" if rnd.random() < 0.75 else "Window", x0 - 0.06, y0 - 0.06, za, x1 + 0.06, y1 + 0.06, zb,
             glass, "Glass", refl=0.15)
    if min(x1 - x0, y1 - y0) > 12:
        cx, cy = (x0 + x1) / 2 + rnd.uniform(-2, 2), (y0 + y1) / 2 + rnd.uniform(-2, 2)
        aabb(m, "Plant room", cx - 3, cy - 2.5, top, cx + 3, cy + 2.5, top + 2.8, (186, 190, 194), "Metal")
    aabb(m, "Parapet", x0 - 0.1, y0 - 0.1, top, x1 + 0.1, y1 + 0.1, top + 0.15, (160, 160, 158), "Concrete")
    return m, top


def tower(parent, cx, cy, w, d, h, glass, frame, z0=0.1, crown=(120, 230, 255)):
    m = new(parent, "Model", "Tower")
    pod = 9.0
    aabb(m, "Podium", cx - w / 2 - 4, cy - d / 2 - 4, z0 - 0.2, cx + w / 2 + 4, cy + d / 2 + 4, z0 + pod,
         rnd.choice(CONC), "Concrete")
    aabb(m, "Shopfront", cx - w / 2 - 4.06, cy - d / 2 - 4.06, z0 + 0.4, cx + w / 2 + 4.06, cy + d / 2 + 4.06, z0 + 4.4,
         (40, 60, 70), "Glass", refl=0.2)
    tiers = [(1.0, 0.6), (0.78, 0.84), (0.56, 1.0)] if h > 100 else [(1.0, 0.75), (0.7, 1.0)] if h > 60 else [(1.0, 1.0)]
    zb = z0 + pod
    for scale, frac in tiers:
        tw, td, zt = w * scale, d * scale, z0 + h * frac
        aabb(m, "Lit window" if rnd.random() < 0.7 else "Window", cx - tw / 2, cy - td / 2, zb, cx + tw / 2,
             cy + td / 2, zt, glass, "Glass", refl=0.22)
        z = zb + 4.0
        while z < zt - 1.5:
            aabb(m, "Spandrel", cx - tw / 2 - 0.25, cy - td / 2 - 0.25, z - 0.45, cx + tw / 2 + 0.25, cy + td / 2 + 0.25,
                 z + 0.45, frame, "Metal")
            z += 4.0
        aabb(m, "Roof", cx - tw / 2 - 0.3, cy - td / 2 - 0.3, zt, cx + tw / 2 + 0.3, cy + td / 2 + 0.3, zt + 0.8, frame,
             "Metal")
        zb = zt + 0.8
    tw, td = w * tiers[-1][0], d * tiers[-1][0]
    x0, y0, x1, y1 = cx - tw / 2 - 0.35, cy - td / 2 - 0.35, cx + tw / 2 + 0.35, cy + td / 2 + 0.35
    for r in ((x0, y0, x1, y0 + 0.5), (x0, y1 - 0.5, x1, y1), (x0, y0 + 0.5, x0 + 0.5, y1 - 0.5),
              (x1 - 0.5, y0 + 0.5, x1, y1 - 0.5)):
        aabb(m, "Crown", r[0], r[1], zb, r[2], r[3], zb + 1.2, crown, "Neon", collide=False)
    vcyl(m, "Antenna", cx, cy, zb, max(6, h * 0.1), 0.5, (200, 200, 205), "Metal")
    ball(m, "Beacon", cx, cy, zb + max(6, h * 0.1), 1.0, (255, 40, 40), "Neon", collide=False)
    return m


HOUSE_WALL = [(236, 228, 214), (214, 196, 170), (190, 210, 220), (226, 212, 190), (204, 220, 198), (240, 236, 228),
              (222, 190, 170)]
HOUSE_ROOF = [(150, 70, 52), (90, 92, 98), (60, 66, 74), (170, 96, 64), (120, 64, 50)]


def house(parent, x, y, f, setback, z0=0.0):
    """A house at (x, y) whose front faces f (a unit vector towards the street)."""
    f = np.array(f, float)
    a = np.array([-f[1], f[0]])
    w, d = rnd.uniform(9, 12), rnd.uniform(8, 10)
    storeys = rnd.choice([1, 1, 2])
    h = 3.2 * storeys
    yaw = math.atan2(f[1], f[0])
    phi = yaw + math.pi / 2
    c = np.array([x, y])
    m = new(parent, "Model", "House")
    ybox(m, "Walls", c[0], c[1], z0 - 0.1, w, d, h + 0.1, phi, rnd.choice(HOUSE_WALL), "Concrete")
    rc = rnd.choice(HOUSE_ROOF)
    for sgn in (1, -1):
        q = c + f * sgn * (d / 4 + 0.25)
        ramp(m, "Roof", q[0], q[1], z0 + h, d / 2 + 0.5, w + 0.8, 2.2, yaw + (math.pi if sgn > 0 else 0), rc, "Slate")
    door = c + f * (d / 2 + 0.03) + a * (w / 2 - 2.0)
    ybox(m, "Door", door[0], door[1], z0, 1.1, 0.08, 2.2, phi, (120, 80, 50), "Wood")
    for st in range(storeys):
        for s_ in ((-w / 4,) if st == 0 else (-w / 4, w / 4 - 0.6)):
            q = c + f * (d / 2 + 0.03) + a * s_
            ybox(m, "Lit window" if rnd.random() < 0.6 else "Window", q[0], q[1], z0 + 3.2 * st + 1.0, 1.8, 0.08, 1.3,
                 phi, (120, 160, 180), "Glass", refl=0.15)
    if rnd.random() < 0.4:
        q = c - f * (d / 4) + a * (w / 2 - 1.5)
        ybox(m, "Chimney", q[0], q[1], z0 + h, 0.8, 0.8, 2.6, phi, (150, 96, 80), "Concrete")
    drive = c + f * (d / 2 + setback / 2) + a * (w / 2 - 2.0)
    ybox(m, "Driveway", drive[0], drive[1], z0 - 0.14, 3.2, setback, 0.2, phi, (184, 180, 172), "Concrete")
    return drive


# ---- suburbs: two blocks of houses down the west side
suburbs = new(city, "Folder", "Suburbs")
car_pad(-33.0, 160.0, 0.0, -28.0, 165.0, 0.0)
for key, (x0, y0, x1, y1) in BLOCKS.items():
    if not key.startswith(("C1R", "C2R")):
        continue
    for f, xh in (((-1.0, 0.0), x0 + SW + 7 + 4.5), ((1.0, 0.0), x1 - SW - 7 - 4.5)):
        for y in np.arange(y0 + SW + 10, y1 - SW - 9, 20):
            fx0, fx1 = (xh - 6, xh + 13) if f[0] > 0 else (xh - 13, xh + 6)      # house and driveway
            if not fits(fx0, y - 7, fx1, y + 7, 2.0):
                continue
            drive = house(suburbs, xh, y, f, 7.0)
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
for key in ("C3R1", "C3R2", "C4R1", "C4R2"):
    x0, y0, x1, y1 = BLOCKS[key]
    paved(midtown, "Paving", x0 + SW, y0 + SW, x1 - SW, y1 - SW, 0.1, 0.25, PAVE, "Slate")
    for c in lots(*BLOCKS[key], 22):
        fx0, fy0 = c[0] + rnd.uniform(1, 3), c[1] + rnd.uniform(1, 3)
        fx1, fy1 = c[2] - rnd.uniform(1, 3), c[3] - rnd.uniform(1, 3)
        if fits(fx0, fy0, fx1, fy1):
            midrise(midtown, fx0, fy0, fx1, fy1, rnd.randint(4, 9), rnd.choice(CONC), rnd.choice(GLASSES))
for q in ((30.0, -130.0), (118.0, -134.0), (30.0, -210.0), (118.0, -210.0)):
    coin(q[0], q[1], 1.1)

# ---- downtown: towers round a plaza with a fountain
downtown = new(city, "Folder", "Downtown")
PLAZA = (180.0, 18.0, 236.0, 74.0)
RESERVED.append(PLAZA)
car_pad(183.0, 52.0, 0.12, 175.5, 52.0, math.pi)
first = True
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
        if key == "C6R3" and first:
            first = False
            tower(downtown, cx, cy, w, d, 232, (36, 70, 96), (230, 232, 234), crown=(255, 120, 220))
            continue
        near = math.hypot(cx - 208, cy - 46)
        h = max(50, rnd.uniform(130, 190) - near * 0.45 + rnd.uniform(-20, 20))
        tower(downtown, cx, cy, w, d, h, rnd.choice(GLASSES), rnd.choice(FRAMES))
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
for key in ("C34R5", "C56R5"):
    x0, y0, x1, y1 = BLOCKS[key]
    paved(uptown, "Paving", x0 + SW, y0 + SW, x1 - SW, y1 - SW, 0.1, 0.25, PAVE, "Slate")
    for c in lots(*BLOCKS[key], 24):
        fx0, fy0, fx1, fy1 = c[0] + 1.5, c[1] + 1.5, c[2] - 1.5, c[3] - 1.5
        if fits(fx0, fy0, fx1, fy1):
            m, top = midrise(uptown, fx0, fy0, fx1, fy1, rnd.randint(6, 13), rnd.choice(BRIGHT), (70, 96, 110),
                             fh=3.2, name="Apartments")
            aabb(m, "Roof garden", fx0 + 1, fy0 + 1, top, fx1 - 1, fy1 - 1, top + 0.12, GRASS, "Grass")
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
    "__STOPS__": "{ %s }" % ", ".join(num(floor_top(i) * K) for i in range(5)),
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
