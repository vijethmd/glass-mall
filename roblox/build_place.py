#!/usr/bin/env python3
"""Build GlassMall.rbxlx: the glass mall as a Roblox place.

The geometry is traced from the same floor plans as ../index.html (page pixels at
200 dpi, 0.0857 m per px). Roblox space: 3.5 studs per metre, X east, Y up, Z south.
Run this, open GlassMall.rbxlx in Roblox Studio, then File > Publish to Roblox.
"""
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
       "Fabric": 1312, "Asphalt": 1376, "Glass": 1568}


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


def light(inst, rng=18, brightness=1.0, color=(255, 236, 210), enabled=True, shadows=False):
    new(inst, "PointLight", "Light", Range=("float", rng), Brightness=("float", brightness), Color=("c3", color),
        Enabled=("bool", enabled), Shadows=("bool", shadows))


# ------------------------------------------------------------------ palette
WHITE, MARBLE, SOFFIT = (243, 243, 240), (228, 224, 216), (236, 236, 233)
GLASS, DOORGLASS, MULL = (160, 200, 212), (176, 212, 222), (176, 184, 190)
CLAD, FRIT, CORE, DARK = (222, 226, 228), (44, 56, 64), (206, 210, 213), (36, 38, 44)
PAVE, WALK, ROAD = (212, 206, 196), (198, 196, 190), (58, 60, 64)
GRASS, TRUNK = (96, 140, 66), (88, 68, 52)

# ------------------------------------------------------------------ the place
game_items = []
ws = Inst("Workspace", "Workspace", StreamingEnabled=("bool", False))
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

# ------------------------------------------------------------------ site
ground = new(site, "Folder", "Ground")
aabb(ground, "Grass", CX - 300, CY - 300, -0.6, CX + 300, CY + 300, -0.08, GRASS, "Grass")
court = [P(950, 733), P(1230, 733), P(1185, 1048), P(830, 876)]
slab(ground, "Entrance court", court, [], 0.0, 0.1, PAVE, "Slate")
slab(ground, "Forecourt", [P(657, 733), P(1395, 733), P(1395, 760), P(657, 760)], [], 0.0, 0.1, PAVE, "Slate")
aabb(ground, "West path", -8.3, 49.6, -0.1, 0.0, 52.8, 0.0, PAVE, "Slate")
diagA, diagB = P(575, 772), P(1474, 1195)
dDir = unit(diagB - diagA)
dOut = np.array([dDir[1], -dDir[0]])             # across the road, away from the mall
phi_road = math.atan2(dDir[1], dDir[0])
road_len = np.linalg.norm(diagB - diagA) + 600
road_mid = (diagA + diagB) / 2


def band(k0, k1, z_top, color, mat, name):
    c = road_mid + dOut * (k0 + k1) / 2
    ybox(ground, name, c[0], c[1], z_top - 0.2, road_len, k1 - k0, 0.2, phi_road, color, mat)


band(0, 5.5, 0.15, WALK, "Concrete", "Pavement")
band(5.5, 25, 0.0, ROAD, "Asphalt", "Main road")
for s in np.arange(-road_len / 2, road_len / 2, 9):
    c = road_mid + dDir * s + dOut * 15.25
    ybox(ground, "Lane mark", c[0], c[1], 0.0, 4, 0.18, 0.012, phi_road, (232, 228, 214), collide=False)
for xa, xb in ((-18.6, -8.3), (70.5, 78.2)):
    aabb(ground, "Side road", xa, CY - 320, -0.2, xb, CY + 320, -0.005, ROAD, "Asphalt")
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
    tr = new(trees, "Model", "Tree")
    vcyl(tr, "Trunk", q[0], q[1], -0.1, h * 0.62, 0.35, TRUNK, "Wood")
    for k in range(6):
        u_, ang = rnd.random(), k * 2.4 + rnd.random()
        d = rr * 0.65 * math.sqrt(u_)
        ball(tr, "Canopy", q[0] + d * math.cos(ang), q[1] + d * math.sin(ang), h * (0.62 + 0.28 * (1 - u_)),
             rr * (0.9 + 0.45 * rnd.random()), rnd.choice(SPECIES[sp]), "Grass", collide=False)

lamps = new(site, "Folder", "StreetLights")
for s in np.arange(-30, 140, 16):
    q = diagA + dDir * s + dOut * 5.2
    lp = new(lamps, "Model", "Street light")
    vcyl(lp, "Pole", q[0], q[1], 0.15, 8.0, 0.18, (70, 74, 78), "Metal")
    hq = q + dOut * 0.7
    head = aabb(lp, "Head", hq[0] - 0.7, hq[1] - 0.2, 7.9, hq[0] + 0.7, hq[1] + 0.2, 8.15, (255, 214, 160))
    light(head, rng=40, brightness=2.2, color=(255, 210, 150), enabled=False)

city = new(site, "Folder", "City")
road_band = lambda p: -6 < float(np.dot(p - diagA, dOut)) < 75
for gx in range(-8, 9):
    for gy in range(-7, 9):
        bx, by = gx * 42 - 10, gy * 42 - 10
        c = np.array([bx + 21, by + 21])
        if np.linalg.norm(c - [CX, CY]) > 300 or rnd.random() < 0.15 or road_band(c):
            continue
        if bx + 42 > -26 and bx < 88 and by + 42 > -12 and by < 100:
            continue
        for _ in range(1 + int(rnd.random() * 3)):
            w, d, h = 10 + rnd.random() * 16, 10 + rnd.random() * 16, 5 + rnd.random() ** 2.8 * 30
            xx, yy = bx + 5 + rnd.random() * max(0, 32 - w), by + 5 + rnd.random() * max(0, 32 - d)
            aabb(city, "Building", xx, yy, -0.1, xx + w, yy + d, h,
                 rnd.choice([(222, 216, 206), (210, 206, 198), (230, 226, 218), (200, 204, 206), (226, 214, 196)]), "Concrete")

cars = new(site, "Folder", "Cars")
for k in range(10):
    q = diagA + dDir * (k * 14) + dOut * (8 + (k % 4) * 4)
    cm = new(cars, "Model", "Car")
    colour = rnd.choice([(232, 232, 230), (40, 44, 50), (140, 146, 150), (183, 59, 47), (31, 59, 92), (220, 218, 212)])
    body = aabb(cm, "Body", q[0] - 0.9, q[1] - 2.15, 0.25, q[0] + 0.9, q[1] + 2.15, 1.05, colour, "SmoothPlastic",
                collide=False, refl=0.1)
    cm.props["PrimaryPart"] = ("ref", body)
    aabb(cm, "Cabin", q[0] - 0.8, q[1] - 1.1, 1.05, q[0] + 0.8, q[1] + 1.0, 1.6, (30, 36, 44), "Glass", collide=False, refl=0.2)
    aabb(cm, "Headlights", q[0] - 0.75, q[1] + 2.15, 0.6, q[0] + 0.75, q[1] + 2.2, 0.8, (255, 246, 220), "Neon", collide=False)
    aabb(cm, "Taillights", q[0] - 0.75, q[1] - 2.2, 0.6, q[0] + 0.75, q[1] - 2.15, 0.8, (220, 40, 30), "Neon", collide=False)

for s in (-10, 20, 50, 80, 110):
    q = diagA + dDir * s + dOut * 2.6
    aabb(wp_street, "Street", q[0] - 0.2, q[1] - 0.2, 0.55, q[0] + 0.2, q[1] + 0.2, 0.95, (255, 0, 0), tr=1,
         collide=False, query=False, shadow=False)
aabb(wp_street, "Street", -7.6, 51.0, 0.4, -7.2, 51.4, 0.8, (255, 0, 0), tr=1, collide=False, query=False, shadow=False)

spawn_c = P(1000, 860)
sp_ = aabb(ws, "SpawnLocation", spawn_c[0] - 1.8, spawn_c[1] - 1.8, -0.05, spawn_c[0] + 1.8, spawn_c[1] + 1.8, 0.05,
           PAVE, "Slate", cls="SpawnLocation")
sp_.props.update(Neutral=("bool", True), Duration=("int", 0), Enabled=("bool", True))

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


start = R3(*(road_mid - dDir * road_len / 2), 0.0)
fill = {
    "__STOPS__": "{ %s }" % ", ".join(num(floor_top(i) * K) for i in range(5)),
    "__ROAD_START__": lua_vec(start),
    "__ROAD_DIR__": lua_vec(D3(dDir[0], dDir[1], 0)),
    "__ROAD_ACROSS__": lua_vec(D3(dOut[0], dOut[1], 0)),
    "__ROAD_LENGTH__": num(road_len * K),
    "__LANES__": "{ %s }" % ", ".join("{ %s, %d }" % (num(o * K), d) for o, d in ((8.2, 1), (11.6, 1), (18.6, -1), (22.0, -1))),
    "__CAR_Y__": num(0.65 * K),
    "__FLOORS__": "{\n%s\n}" % ",\n".join('\t{ y = %s, name = "%s", note = "%s" }' % (num(floor_top(i) * K), l[0], l[4])
                                          for i, l in enumerate(LEVELS)),
    "__FOOTPRINTS__": "{\n%s\n}" % ",\n".join("\t{ %s }" % ", ".join("{ %s, %s }" % (num(R3(p[0], p[1], 0)[0]), num(R3(p[0], p[1], 0)[2]))
                                                                         for p in POLY[l[3]]) for l in LEVELS),
    "__TERRACE__": "{ %s }" % ", ".join("{ %s, %s }" % (num(R3(p[0], p[1], 0)[0]), num(R3(p[0], p[1], 0)[2])) for p in tri),
}


def script_src(fname):
    src = (SCRIPTS / fname).read_text()
    for k, v in fill.items():
        src = src.replace(k, v)
    assert "__" not in src.replace("__index", ""), fname
    return src


sss = Inst("ServerScriptService", "ServerScriptService")
game_items.append(sss)
for f in sorted(SCRIPTS.glob("*.server.lua")):
    new(sss, "Script", f.name.split(".")[0], Source=("src", script_src(f.name)))
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
