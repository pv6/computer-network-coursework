import numpy as np
from receiver_and_sender import Receiver, Sender, Transmitter
from multiprocessing import Queue, Process, Manager, Array


class Sensor:
    def __init__(self, sensor_centre, sensor_height, sensor_id, swindler=False):
        self.sensor_centre = sensor_centre.copy()
        self.sensor_height = sensor_height
        self.swindler = swindler
        self.intersections = []
        self.senders = []
        self.transmitters = []
        self.receivers = []
        self.data_from_receiver = []
        self.received_data = {}
        self.received_data_sets = {}
        self.sensor_id = sensor_id

    def get_receivers_and_data(self):
        return self.receivers, self.data_from_receiver

    def set_sender_receiver_parameters(self, senders, transmitters, receivers, receivers_data):
        self.senders = senders
        self.transmitters = transmitters
        self.receivers = receivers
        self.data_from_receiver = receivers_data

    def set_sender_transmitter(self, senders, transmitters):
        self.senders = senders
        self.transmitters = transmitters

    def get_sender_receiver_parameters(self):
        return self.transmitters, self.senders, self.receivers

    def generate_rand_points(self):
        points_num = len(self.intersections)
        rand_points = []
        for i in range(points_num):
            rand_points.append([np.random.rand(), np.random.rand()])
        return rand_points

    def generate_rand_points_array(self, size_arr):
        rand_points = []
        for i in range(size_arr):
            rand_points.append(np.random.rand())
        return rand_points

    def send_broadcast_intersections(self, corruption_p, receivers, data):
        num_packages = len(self.intersections)  # number of packages
        receivers_num = len(self.transmitters)
        send_data = self.intersections.copy()
        for i in range(receivers_num):
            if self.swindler:
                send_data = self.generate_rand_points()
            sender_proc = Process(target=self.senders[i].send, args=(num_packages, corruption_p, send_data))
            receiver_proc = Process(target=receivers[i].receive, args=(num_packages, data[i], ))
            sender_proc.start()
            receiver_proc.start()
            receiver_proc.join()
            sender_proc.join()

    def send_broadcast_set_intersections(self, corruption_p, receivers, data):
        num_packages = len(self.received_data)  # number of packages
        receivers_num = len(self.transmitters)
        send_data = []
        for i in range(1, num_packages + 1):
            send_data.append(self.received_data[i])
        size = len(send_data)
        if self.swindler == True:
            send_data.clear()
            for i in range(size):
                send_data.append(self.generate_rand_points())
        for i in range(receivers_num):
            sender_proc = Process(target=self.senders[i].send, args=(num_packages, corruption_p, send_data))
            receiver_proc = Process(target=receivers[i].receive, args=(num_packages, data[i], ))
            sender_proc.start()
            receiver_proc.start()
            receiver_proc.join()
            sender_proc.join()

    def set_received_data(self, sensors_num):
        self.received_data = {a: [] for a in range(1, sensors_num + 1)}
        other_sensors_ids = []
        for i in range(1, sensors_num + 1):
            if i != self.sensor_id:
                other_sensors_ids.append(i)

        self.received_data[self.sensor_id] = self.intersections
        for i in range(len(self.receivers)):
            tmp_list = []
            for j in range(len(self.data_from_receiver[i])):
                tmp_list.append(self.data_from_receiver[i][j])
            self.received_data[other_sensors_ids[i]] = tmp_list

    def set_received_data_2(self, sensors_num):
        this_sensor_data = []
        for i in range(1, len(self.received_data) + 1):
            this_sensor_data.append(self.received_data[i])

        self.received_data_sets = {a: [] for a in range(1, sensors_num + 1)}
        other_sensors_ids = []
        for i in range(1, sensors_num + 1):
            if i != self.sensor_id:
                other_sensors_ids.append(i)

        self.received_data_sets[self.sensor_id] = this_sensor_data
        for i in range(len(self.receivers)):
            tmp_list = []
            for j in range(len(self.data_from_receiver[i])):
                tmp_list.append(self.data_from_receiver[i][j])
            self.received_data_sets[other_sensors_ids[i]] = tmp_list

    def make_result_vector(self):
        res_vector = [[], [], [], []]
        size = len(self.received_data_sets)
        for k in range(size):
            tmp_list = []
            for i in range(1, size + 1):
                tmp_list.append(self.received_data_sets[i][k])
            for point in tmp_list:
                if tmp_list.count(point) > 1:
                    res_vector[k] = point
                    break
        return res_vector

    def send_result_vector_to_router(self, corruption_p, receiver, data):
        res_vector = self.make_result_vector()
        num_packages = len(res_vector)
        sender_proc = Process(target=self.senders[0].send, args=(num_packages, corruption_p, res_vector))
        receiver_proc = Process(target=receiver.receive, args=(num_packages, data))
        sender_proc.start()
        receiver_proc.start()
        receiver_proc.join()
        sender_proc.join()


def calculate_sensor_parameters(square_num, screen_centre, screen_height):
    sensor_centre = [0, 0]
    if square_num == 1:
        sensor_centre[0] = screen_centre[0] - screen_height / 4
        sensor_centre[1] = screen_centre[1] - screen_height / 4
    elif square_num == 2:
        sensor_centre[0] = screen_centre[0] - screen_height / 4
        sensor_centre[1] = screen_centre[1] + screen_height / 4
    elif square_num == 3:
        sensor_centre[0] = screen_centre[0] + screen_height / 4
        sensor_centre[1] = screen_centre[1] + screen_height / 4
    elif square_num == 4:
        sensor_centre[0] = screen_centre[0] + screen_height / 4
        sensor_centre[1] = screen_centre[1] - screen_height / 4
    return sensor_centre, screen_height/2


class DesignatedRouter:
    def __init__(self, screen_centre, screen_height):
        self.sensors_num = 4
        self.sensor_1 = Sensor(*calculate_sensor_parameters(1, screen_centre, screen_height), sensor_id=1)
        self.sensor_2 = Sensor(*calculate_sensor_parameters(2, screen_centre, screen_height), sensor_id=2)
        self.sensor_3 = Sensor(*calculate_sensor_parameters(3, screen_centre, screen_height), sensor_id=3, swindler=True)
        self.sensor_4 = Sensor(*calculate_sensor_parameters(4, screen_centre, screen_height), sensor_id=4)
        self.data_from_sensors = []

    def set_intersections_for_sensors(self, intersections_sensor1, intersections_sensor2,
                                      intersections_sensor3, intersections_sensor4, centre_square):
        if len(intersections_sensor1) > 0 or centre_square == 1:
            self.sensor_1.intersections = intersections_sensor1
        if len(intersections_sensor2) > 0 or centre_square == 2:
            self.sensor_2.intersections = intersections_sensor2
        if len(intersections_sensor3) > 0 or centre_square == 3:
            self.sensor_3.intersections = intersections_sensor3
        if len(intersections_sensor4) > 0 or centre_square == 4:
            self.sensor_4.intersections = intersections_sensor4

    def get_points(self):
        points1 = self.sensor_1.intersections
        points2 = self.sensor_2.intersections
        points3 = self.sensor_3.intersections
        points4 = self.sensor_4.intersections
        return points1 + points2 + points3 + points4

    def set_sender_receiver_parameters(self, protocol, window_size, receivers_num, arr_size):
        transmitters_1, transmitters_2, transmitters_3, transmitters_4 = [], [], [], []
        senders_1, senders_2, senders_3, senders_4 = [], [], [], []
        receivers_1, receivers_2, receivers_3, receivers_4 = [], [], [], []
        receivers_data_1, receivers_data_2, receivers_data_3, receivers_data_4 = [], [], [], []
        manager = Manager()
        for i in range(receivers_num):
            transmitters_1.append(Transmitter(Queue(), Queue()))
            transmitters_2.append(Transmitter(Queue(), Queue()))
            transmitters_3.append(Transmitter(Queue(), Queue()))
            transmitters_4.append(Transmitter(Queue(), Queue()))
            receivers_1.append(Receiver(transmitters_1[i], protocol, window_size))
            receivers_2.append(Receiver(transmitters_2[i], protocol, window_size))
            receivers_3.append(Receiver(transmitters_3[i], protocol, window_size))
            receivers_4.append(Receiver(transmitters_4[i], protocol, window_size))
            receivers_data_1.append(manager.list())
            receivers_data_2.append(manager.list())
            receivers_data_3.append(manager.list())
            receivers_data_4.append(manager.list())

        senders_1.append(Sender(transmitters_2[0], protocol, window_size))
        senders_1.append(Sender(transmitters_3[0], protocol, window_size))
        senders_1.append(Sender(transmitters_4[0], protocol, window_size))

        senders_2.append(Sender(transmitters_1[0], protocol, window_size))
        senders_2.append(Sender(transmitters_3[1], protocol, window_size))
        senders_2.append(Sender(transmitters_4[1], protocol, window_size))

        senders_3.append(Sender(transmitters_1[1], protocol, window_size))
        senders_3.append(Sender(transmitters_2[1], protocol, window_size))
        senders_3.append(Sender(transmitters_4[2], protocol, window_size))

        senders_4.append(Sender(transmitters_1[2], protocol, window_size))
        senders_4.append(Sender(transmitters_2[2], protocol, window_size))
        senders_4.append(Sender(transmitters_3[2], protocol, window_size))

        self.sensor_1.set_sender_receiver_parameters(senders_1, transmitters_1, receivers_1, receivers_data_1)
        self.sensor_2.set_sender_receiver_parameters(senders_2, transmitters_2, receivers_2, receivers_data_2)
        self.sensor_3.set_sender_receiver_parameters(senders_3, transmitters_3, receivers_3, receivers_data_3)
        self.sensor_4.set_sender_receiver_parameters(senders_4, transmitters_4, receivers_4, receivers_data_4)

    def set_sender_receiver_parameters_one_receiver(self, protocol, window_size):
        transmitters_1, transmitters_2, transmitters_3, transmitters_4 = [], [], [], []
        senders_1, senders_2, senders_3, senders_4 = [], [], [], []

        transmitters_1.append(Transmitter(Queue(), Queue()))
        transmitters_2.append(Transmitter(Queue(), Queue()))
        transmitters_3.append(Transmitter(Queue(), Queue()))
        transmitters_4.append(Transmitter(Queue(), Queue()))

        senders_1.append(Sender(transmitters_1[0], protocol, window_size))
        senders_2.append(Sender(transmitters_2[0], protocol, window_size))
        senders_3.append(Sender(transmitters_3[0], protocol, window_size))
        senders_4.append(Sender(transmitters_4[0], protocol, window_size))

        self.sensor_1.set_sender_transmitter(senders_1, transmitters_1)
        self.sensor_2.set_sender_transmitter(senders_2, transmitters_2)
        self.sensor_3.set_sender_transmitter(senders_3, transmitters_3)
        self.sensor_4.set_sender_transmitter(senders_4, transmitters_4)

    def process_send_receive_intersections(self, corruption_p):
        receivers_1, data_1 = self.sensor_1.get_receivers_and_data()
        receivers_2, data_2 = self.sensor_2.get_receivers_and_data()
        receivers_3, data_3 = self.sensor_3.get_receivers_and_data()
        receivers_4, data_4 = self.sensor_4.get_receivers_and_data()

        self.sensor_1.send_broadcast_intersections(corruption_p, [receivers_2[0], receivers_3[0], receivers_4[0]],
                                                   [data_2[0], data_3[0], data_4[0]])
        self.sensor_2.send_broadcast_intersections(corruption_p, [receivers_1[0], receivers_3[1], receivers_4[1]],
                                                   [data_1[0], data_3[1], data_4[1]])
        self.sensor_3.send_broadcast_intersections(corruption_p, [receivers_1[1], receivers_2[1], receivers_4[2]],
                                                   [data_1[1], data_2[1], data_4[2]])
        self.sensor_4.send_broadcast_intersections(corruption_p, [receivers_1[2], receivers_2[2], receivers_3[2]],
                                                   [data_1[2], data_2[2], data_3[2]])
        print('Формирование вектора с координатами точек пересечения, полученными от других узлов')
        self.sensor_1.set_received_data(self.sensors_num)
        self.sensor_2.set_received_data(self.sensors_num)
        self.sensor_3.set_received_data(self.sensors_num)
        self.sensor_4.set_received_data(self.sensors_num)

    def process_send_receive_sets(self, corruption_p):
        receivers_1, data_1 = self.sensor_1.get_receivers_and_data()
        receivers_2, data_2 = self.sensor_2.get_receivers_and_data()
        receivers_3, data_3 = self.sensor_3.get_receivers_and_data()
        receivers_4, data_4 = self.sensor_4.get_receivers_and_data()

        self.sensor_1.send_broadcast_set_intersections(corruption_p, [receivers_2[0], receivers_3[0], receivers_4[0]],
                                                       [data_2[0], data_3[0], data_4[0]])
        self.sensor_2.send_broadcast_set_intersections(corruption_p, [receivers_1[0], receivers_3[1], receivers_4[1]],
                                                       [data_1[0], data_3[1], data_4[1]])
        self.sensor_3.send_broadcast_set_intersections(corruption_p, [receivers_1[1], receivers_2[1], receivers_4[2]],
                                                       [data_1[1], data_2[1], data_4[2]])
        self.sensor_4.send_broadcast_set_intersections(corruption_p, [receivers_1[2], receivers_2[2], receivers_3[2]],
                                                       [data_1[2], data_2[2], data_3[2]])
        print('Формирование набора векторов, полученными от других узлов')
        self.sensor_1.set_received_data_2(self.sensors_num)
        self.sensor_2.set_received_data_2(self.sensors_num)
        self.sensor_3.set_received_data_2(self.sensors_num)
        self.sensor_4.set_received_data_2(self.sensors_num)

    def receive_points_from_sensors(self, protocol, window_size, corruption_p):
        receiver_1 = Receiver(self.sensor_1.transmitters[0], protocol, window_size)
        receiver_2 = Receiver(self.sensor_2.transmitters[0], protocol, window_size)
        receiver_3 = Receiver(self.sensor_3.transmitters[0], protocol, window_size)
        receiver_4 = Receiver(self.sensor_4.transmitters[0], protocol, window_size)
        manager = Manager()
        data_1 = manager.list()
        data_2 = manager.list()
        data_3 = manager.list()
        data_4 = manager.list()

        print('Создание результирующего вектора')
        print('Передача результирующего вектора на роутер')
        self.sensor_1.send_result_vector_to_router(corruption_p, receiver_1, data_1)
        self.sensor_2.send_result_vector_to_router(corruption_p, receiver_2, data_2)
        self.sensor_3.send_result_vector_to_router(corruption_p, receiver_3, data_3)
        self.sensor_4.send_result_vector_to_router(corruption_p, receiver_4, data_4)

        all_vectors = [data_1, data_2, data_3, data_4]

        return all_vectors

    def process_get_data_from_sensors(self, protocol, window_size):
        corruption_p = 0
        print('Начало решения Византийской задачи')
        self.set_sender_receiver_parameters(protocol, window_size, self.sensors_num - 1, 4)
        print('Рассылка сообщения с координатами точек пересечения всем узлам сети')
        self.process_send_receive_intersections(corruption_p)
        self.set_sender_receiver_parameters(protocol, window_size, self.sensors_num - 1, 12)
        print('Рассылка сообщения с вектором, содержащим координаты точек пересечения, всем узлам сети')
        self.process_send_receive_sets(corruption_p)
        self.set_sender_receiver_parameters_one_receiver(protocol, window_size)
        self.data_from_sensors = self.receive_points_from_sensors(protocol, window_size, corruption_p)

    def calculate_new_centre(self):
        print('Расчет центра окружности по полученным точкам')
        size = len(self.data_from_sensors)
        points = []
        for i in range(size):
            if len(self.data_from_sensors[0][i]) != 0:
                points.append(self.data_from_sensors[0][i][0])
                points.append(self.data_from_sensors[0][i][1])

        if len(points) <= 2:
            print ('cant calculate new centre')
            return [np.nan, np.nan]

        point1 = points[0]
        point2 = [np.nan, np.nan]
        point3 = [np.nan, np.nan]
        for point in points:
            if point[0] != point1[0] or point[1] != point1[1]:
                point2 = point
        for point in points:
            if ((point[0] != point1[0] or point[1] != point1[1]) and
                    (point[0] != point2[0] or point[1] != point2[1])):
                point3 = point

        if (point2[0] is np.nan) or (point3[0] is np.nan):
            print ('cant calculate new centre')
            return [np.nan, np.nan]

        A = point2[0] - point1[0]
        B = point2[1] - point1[1]
        C = point3[0] - point1[0]
        D = point3[1] - point1[1]
        E = A * (point2[0] + point1[0]) + B * (point2[1] + point1[1])
        F = C * (point3[0] + point1[0]) + D * (point3[1] + point1[1])
        G = 2 * (A * (point3[1] - point2[1]) - B * (point3[0] - point2[0]))
        Cx = (D * E - B * F) / G
        Cy = (A * F - C * E) / G
        centre = [Cx, Cy]
        return centre


