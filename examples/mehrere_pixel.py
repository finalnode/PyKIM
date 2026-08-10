"""Drei Pixel unabhängig in derselben Welt malen lassen."""

from pykim import kim, world


# Die Geschwindigkeit gehört zur gemeinsamen Welt.
world.speed(30)

# KIM ist bereits vorhanden und zeichnet einen violetten Winkel.
kim.set_position(20, 20)
kim.paint_path("purple")

# Weitere Pixel werden von der Welt erzeugt und haben einen eigenen Zustand.
mia = world.new_pixel("MIA", x=60, y=20)
mia.paint_path("orange")

leo = world.new_pixel("LEO", x=40, y=60)
leo.paint_path("cyan")

# Phase 1: Alle drei bewegen sich gleichzeitig aufeinander zu.
with world.parallel():
    kim.right(15)
    mia.left(15)
    leo.up(20)

# Phase 2: Außerhalb des Blocks laufen die Befehle nacheinander.
kim.down(10)
mia.down(20)
leo.right(10)

# Phase 3: Zum Abschluss bewegen sich alle wieder gleichzeitig.
with world.parallel():
    kim.right(15)
    mia.left(15)
    leo.up(15)

leo.hide()  # Die cyanfarbene Spur bleibt sichtbar, LEO selbst verschwindet.

# Alle drei Pixel und ihre Spuren erscheinen im selben Fenster.
world.run(check="mehrere-pixel")
