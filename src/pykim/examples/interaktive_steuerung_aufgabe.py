"""Musterlösung: Der Übergang von PyKIM zur Pyxel-Spielschleife."""


from pykim import kim, world

kim.position = (80, 60)


def update():
    if world.btn("left") and kim.x > 0:
        kim.left()
    if world.btn("right") and kim.x < world.width - 1:
        kim.right()
    if world.btn("up") and kim.y > 0:
        kim.up()
    if world.btn("down") and kim.y < world.height - 1:
        kim.down()


def draw():
    world.cls("black")
    world.text(5, 5, "Bewege KIM mit den Pfeiltasten", "white")
    kim.draw()


world.run(update, draw, check="interaktive-steuerung")
