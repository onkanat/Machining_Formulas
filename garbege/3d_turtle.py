import time
from turtles3D import Turtle3D

def connect(t: Turtle3D, point1, point2):
    """Helper function to draw a connecting line between 2 points"""

    start = t.pos()
    d = t.isdown()
    t.penup()
    t.goto(point1)
    t.pendown()
    t.goto(point2)
    t.penup()
    t.goto(start)
    if d:
        t.pendown()

def draw_axes(t: Turtle3D):
    """Helper function to draw the x,y, and z axes in different colors to help visualize where they are"""

    t.pencolor("blue")
    t.goto(500, 0, 0)
    t.write("X")
    t.goto(-500, 0, 0)
    t.write("-X")
    t.home()
    t.pencolor("red")
    t.goto(0, 500, 0)
    t.write("Y")
    t.goto(0, -500, 0)
    t.write("-Y")
    t.home()
    t.pencolor("green")
    t.goto(0, 0, 500)
    t.write("Z")
    t.goto(0, 0, -500)
    t.write("-Z")
    t.home()
    t.pencolor("black")

def run(t: Turtle3D):
    """Main function to handle our drawing and animation"""

    # here we define the eight points that make up the corners of our cube
    points = [
        [50, -50, -50],  # bottom-right-front
        [50, 50, -50],  # top-right-front
        [-50, 50, -50],  # top-left-front
        [-50, -50, -50],  # bottom-left-front
        [50, -50, 50],  # bottom-right-back
        [50, 50, 50],  # top-right-back
        [-50, 50, 50],  # top-left-back
        [-50, -50, 50],  # bottom-left-back
    ]

    # connecting each of the points to the other points it needs to
    for i in range(4):
        connect(t, points[i], points[(i + 1) % 4])
        connect(t, points[i + 4], points[((i + 1) % 4) + 4])
        connect(t, points[i], points[i + 4])


    # animating 2 degree rotations of each axis 10,000 times
    angle = 2
    for i in range(10000):

        t.rotateX(angle, False) # False because we don't want to redraw the lines until the final rotation
        t.rotateY(angle, False)
        t.rotateZ(angle)

        time.sleep(1 / 60) # so we are redrawing 60 times per second. not exactly equal to 60fps due draw times, but pretty close.


if __name__ == "__main__":
    t = Turtle3D()
    s = t.getscreen()

    draw_axes(t) # comment out this line for smoother animation

    run(t)
    s.exitonclick()
