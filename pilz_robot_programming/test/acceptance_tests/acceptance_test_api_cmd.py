#!/usr/bin/env python
# Copyright (c) 2018 Pilz GmbH & Co. KG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from geometry_msgs.msg import Point
from pilz_robot_programming.robot import *
from pilz_robot_programming.commands import *
from pilz_industrial_motion_testutils.acceptance_test_utils import _askPermission, _askSuccess

from pilz_robot_tfc_api.modbus_tfc_api import ModbusTfcAPI
from pilz_robot_tfc_api.pilz_modbus_client import PilzModbusClient
from pilz_robot_tfc_api.op_modes import OperationMode

PTP_VEL_PICK = 0.1

_REQUIRED_API_VERSION = "1"


def start_program():
    print("Executing " + __file__)

    robot = Robot(_REQUIRED_API_VERSION)

    _test_ptp_pos(robot)
    _test_lin_pos(robot)
    _test_circ_pos(robot)
    _test_blend_pos(robot)
    _test_seq_pos1(robot)
    _test_seq_pos2(robot)


def _test_ptp_pos(robot):
    """Tests a ptp motion.

        Test Sequence:
          1. Move to zero position
          2. Move away from the singularity.

        Expected Results:
          1. Robot moves to zero position.
          2. Robot moves away from the singularity.
    """
    tfc = ModbusTfcAPI(PilzModbusClient())
    tfc.open()

    tfc.disable_emergency()
    tfc.acknowledge_ready_signal()

    tfc.choose_operation_mode(OperationMode.T1)
    tfc.acknowledge_ready_signal()

    tfc.activate_enabling()
    # Wait till enabling is given by FS controller
    time.sleep(0.5)

    robot.move(Ptp(goal=[0, 0, 0, 0, 0, 0]))
    robot.move(Ptp(goal=[0, -0.78, 0.78, 0, 1.56, 0]))

    tfc.deactivate_enabling()
    tfc.close()

    # TODO: Check that robot moved to [0,0,0,0,0,0] and after that away from [0,0,0,0,0,0]


def _test_lin_pos(robot):
    """Test a lin motion

        Test Sequence:
          1. Move to start position using Ptp (upper "pick" position)
          2. Move 15cm linear down.
          3. Move 15cm linear up.

        Expected Results:
          1. Robot moves to the upper "pick" position
          2. Robot moves 15cm linear down.
          3. Robot moves 15cm linear up.
    """

    tfc = ModbusTfcAPI(PilzModbusClient())
    tfc.open()

    tfc.disable_emergency()
    tfc.acknowledge_ready_signal()

    tfc.choose_operation_mode(OperationMode.T1)
    tfc.acknowledge_ready_signal()

    tfc.activate_enabling()
    # Wait till enabling is given by FS controller
    time.sleep(0.5)

    robot.move(Ptp(goal=Pose(position=Point(-0.46, -0.21, 0.19), orientation=from_euler(0, -3.14, -0.25))))
    robot.move(Lin(goal=Pose(position=Point(0.0, 0.0, -0.15)), relative=True, vel_scale=PTP_VEL_PICK))
    robot.move(Lin(goal=Pose(position=Point(0.0, 0.0, 0.15)), relative=True, vel_scale=PTP_VEL_PICK))

    tfc.deactivate_enabling()
    tfc.close()

    # TODO: Check that robot has moved to the upper pick position, then  linear 15cm down and then linear 15cm up


def _test_seq_pos1(robot):
    """Tests a motion sequence. Together the two tests _test_seq_pos1 and _test_seq_pos2 contain all possible pairs of
    consecutive commands from the set of commands (PTP, LIN, CIRC).

        Test Sequence:
            1. Execute sequence (PTP-PTP-LIN-LIN-CIRC-CIRC-PTP) consisting of the following motions:
                a. Move to zero position.
                b. Move to the upper "pick" position.
                c. Move 15cm linear down.
                d. Move 15cm linear up.
                e. Move a quarter circle.
                f. Move back the quarter circle.
                g. Move back to zero position.

        Expected Results:
            1. Robot performes sequence of the following motions stopping in between them:
                a. Robot moves to zero position.
                b. Robot moves to the upper "pick" position.
                c. Robot moves 15cm linear down.
                d. Robot moves 15cm linear up.
                e. Robot moves a quarter circle.
                f. Robot moves back the quarter circle.
                g. Robot moves back to zero position.
    """
    tfc = ModbusTfcAPI(PilzModbusClient())
    tfc.open()

    tfc.disable_emergency()
    tfc.acknowledge_ready_signal()

    tfc.choose_operation_mode(OperationMode.T1)
    tfc.acknowledge_ready_signal()

    tfc.activate_enabling()
    # Wait till enabling is given by FS controller
    time.sleep(0.5)

    x_pick = 0
    y_pick = 0.25
    z_pick_low = 0.25
    z_pick_high = 0.4

    x_pick2 = -0.25
    y_pick2 = 0

    x_center = y_center = 0

    rot = Quaternion(0.0, 1.0, 0.0, 0.0)
    p_pick_high = Pose(position=Point(x_pick, y_pick, z_pick_high), orientation=rot)
    p_pick_low = Pose(position=Point(x_pick,  y_pick, z_pick_low),  orientation=rot)
    p_pick_high2 = Pose(position=Point(x_pick2, y_pick2, z_pick_high), orientation=rot)
    p_center = Pose(position=Point(x_center, y_center, z_pick_high))

    seq_l = Sequence()
    seq_l.append(Ptp(goal=[0, 0, 0, 0, 0, 0]))
    seq_l.append(Ptp(goal=p_pick_high))
    seq_l.append(Lin(goal=p_pick_low))
    seq_l.append(Lin(goal=p_pick_high))
    seq_l.append(Circ(goal=p_pick_high2, center=p_center.position))
    seq_l.append(Circ(goal=p_pick_high, center=p_center.position))
    seq_l.append(Ptp(goal=[0, 0, 0, 0, 0, 0]))

    robot.move(seq_l)

    tfc.deactivate_enabling()
    tfc.close()

    # TODO Check that robot  moved to [0,0,0,0,0,0] and then to the upper pick position,
    #  After that the robot tcp should have moved linear 15cm down and then linear 15cm up.
    #  Further on the robot should have moved a quarter circle forwards and backwards and then back to [0,0,0,0,0,0].


def _test_seq_pos2(robot):
    """Tests a motion sequence. Together the two tests _test_seq_pos1 and _test_seq_pos2 contain all possible pairs of
    consecutive commands from the set of commands (PTP, LIN, CIRC).

        Test Sequence:
            1. Execute sequence (PTP-CIRC-LIN-LIN-PTP) consisting of the following motions:
                a. Move to specific start position.
                b. Move a quarter circle arriving at the upper "pick" position.
                c. Move 15cm linear down.
                d. Move 15cm linear up.
                e. Move back to zero position.

        Expected Results:
            1. Robot performes sequence of the following motions stopping in between them:
                a. Robot moves to specific start position.
                b. Robot moves a quarter circle arriving at the upper "pick" position.
                c. Robot moves 15cm linear down.
                d. Robot moves 15cm linear up.
                e. Robot moves back to zero position.
    """
    tfc = ModbusTfcAPI(PilzModbusClient())
    tfc.open()

    tfc.disable_emergency()
    tfc.acknowledge_ready_signal()

    tfc.choose_operation_mode(OperationMode.T1)
    tfc.acknowledge_ready_signal()

    tfc.activate_enabling()
    # Wait till enabling is given by FS controller
    time.sleep(0.5)

    x_pick = 0
    y_pick = 0.25
    z_pick_low = 0.25
    z_pick_high = 0.4

    x_pick2 = -0.25
    y_pick2 = 0

    x_center = y_center = 0

    rot = Quaternion(0.0, 1.0, 0.0, 0.0)
    p_pick_high = Pose(position=Point(x_pick, y_pick, z_pick_high), orientation=rot)
    p_pick_low = Pose(position=Point(x_pick,  y_pick, z_pick_low),  orientation=rot)
    p_pick_high2 = Pose(position=Point(x_pick2, y_pick2, z_pick_high), orientation=rot)
    p_center = Pose(position=Point(x_center, y_center, z_pick_high))

    seq_l = Sequence()
    seq_l.append(Ptp(goal=p_pick_high2))
    seq_l.append(Circ(goal=p_pick_high, center=p_center.position))
    seq_l.append(Lin(goal=p_pick_low))
    seq_l.append(Lin(goal=p_pick_high))
    seq_l.append(Ptp(goal=[0, 0, 0, 0, 0, 0]))

    robot.move(seq_l)

    tfc.deactivate_enabling()
    tfc.close()

    # TODO Check that robot moved to a start position and then a quarter circle arriving at the upper pick position.
    #  After that the robot tcp should have moved linear 15cm down and then linear 15cm up.
    #  In the end the robot should have moved back to [0,0,0,0,0,0].


def _test_circ_pos(robot):
    """Test a circ motion

        Test Sequence:
          1. Move to start position using Ptp (upper "pick" position)
          2. Move half a circle.
          3. Move half a circle back to origin.

        Expected Results:
          1. Robot moves to start position.
          2. Robot moves half a circle.
          3. Robot moves half a circle back to origin.
    """
    tfc = ModbusTfcAPI(PilzModbusClient())
    tfc.open()

    tfc.disable_emergency()
    tfc.acknowledge_ready_signal()

    tfc.choose_operation_mode(OperationMode.T1)
    tfc.acknowledge_ready_signal()

    tfc.activate_enabling()
    # Wait till enabling is given by FS controller
    time.sleep(0.5)

    robot.move(Ptp(goal=Pose(position=Point(-0.46, -0.21, 0.19), orientation=from_euler(0, -3.14, -0.25))))

    robot.move(Circ(goal=Pose(position=Point(-0.460, 0, 0.19),
                    orientation=from_euler(0, -3.14, -0.25)), vel_scale=PTP_VEL_PICK,
                    interim=Point(-0.355, -0.105, 0.19)))

    robot.move(Circ(goal=Pose(position=Point(-0.460, -0.21, 0.19),
                    orientation=from_euler(0, -3.14, -0.25)), vel_scale=PTP_VEL_PICK,
                    interim=Point(-0.565, -0.105, 0.19)))

    tfc.deactivate_enabling()
    tfc.close()

    # TODO Check that robot moved to a start position and then two times half a circle


def _test_blend_pos(robot):
    """ Test a motion blending

        Test Sequence:
          1. Move to start position using Ptp (upper "pick" position)
          2. Generate square movement by blending 4 lin.

        Expected Results:
          1. Robot moves to start position.
          2. Robot moves in a square without intermediate stops.
    """
    tfc = ModbusTfcAPI(PilzModbusClient())
    tfc.open()

    tfc.disable_emergency()
    tfc.acknowledge_ready_signal()

    tfc.choose_operation_mode(OperationMode.T1)
    tfc.acknowledge_ready_signal()

    tfc.activate_enabling()
    # Wait till enabling is given by FS controller
    time.sleep(0.5)

    robot.move(Ptp(goal=Pose(position=Point(-0.46, -0.21, 0.19), orientation=from_euler(0, -3.14, -0.25))))

    seq_l = Sequence()
    seq_l.append(Lin(goal=Pose(position=Point(-0.460, 0, 0.19),
                       orientation=from_euler(0, -3.14, -0.25)), vel_scale=PTP_VEL_PICK), blend_radius=0.05)

    seq_l.append(Lin(goal=Pose(position=Point(-0.3, 0, 0.19),
                       orientation=from_euler(0, -3.14, -0.25)), vel_scale=PTP_VEL_PICK), blend_radius=0.05)

    seq_l.append(Lin(goal=Pose(position=Point(-0.3, -0.21, 0.19),
                       orientation=from_euler(0, -3.14, -0.25)), vel_scale=PTP_VEL_PICK), blend_radius=0.05)

    seq_l.append(Lin(goal=Pose(position=Point(-0.46, -0.21, 0.19),
                       orientation=from_euler(0, -3.14, -0.25)), vel_scale=PTP_VEL_PICK), blend_radius=0.0)

    robot.move(seq_l)

    tfc.deactivate_enabling()
    tfc.close()

    # TODO Check that robot  moved to a start position and then in a square always returning to the start position.
    #  During the motion the robot does not stop.


if __name__ == "__main__":
    # Init a ros node
    rospy.init_node('api_acceptance_tests_node', anonymous=True)

    start_program()
