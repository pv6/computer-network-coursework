from screen import Screen
from sensor import DesignatedRouter


if __name__ == "__main__":
    screen_centre = [3, 1]
    screen_height = 2
    spot_diam = 1.1
    move_step = 0.2

    screen = Screen(screen_centre, screen_height, spot_diam, move_step)
    for i in range(3):
        router = DesignatedRouter(screen_centre, screen_height)
        screen.makePlotSpotAndIntersections()
        screen.randMoveSpot()

        router.set_intersections_for_sensors(*screen.intersectionsWithSensors())
        router.process_get_data_from_sensors(0, 2)
        new_centre = router.calculate_new_centre()
        print('Центр окружности: ', new_centre)
