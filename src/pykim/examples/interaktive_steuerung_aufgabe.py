"""Musterlösung: Der Übergang von PyKIM zur Pyxel-Spielschleife."""


from pykim import kim, world

kim.set_position(80, 60)


def update():
    if world.btn("left") and kim.get_x() > 0:
        kim.left()
    if world.btn("right") and kim.get_x() < world.width - 1:
        kim.right()
    if world.btn("up") and kim.get_y() > 0:
        kim.up()
    if world.btn("down") and kim.get_y() < world.height - 1:
        kim.down()


def draw():
    world.cls("black")
    world.text(5, 5, "Bewege KIM mit den Pfeiltasten", "white")
    kim.draw()


world.run(update, draw, check="interaktive-steuerung")
