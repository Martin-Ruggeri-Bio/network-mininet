#!/usr/bin_/python

from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from subprocess import call
import argparse

def myNetwork():

   parser = argparse.ArgumentParser()
   parser.add_argument("sucursales", help="Cantidad de sucursales a crear", type=int)
   args = parser.parse_args()
   switches_wan = []
   switches_lan = []
   routers = []
   hosts = []
   wan_mask = 29
   lan_mask = 24

   net = Mininet( topo=None,
                  build=False,
                  ipBase='10.0.0.0/8')

   info( '*** Adding controller\n' )
   info( '*** Add switches\n')
   for i in range(args.sucursales):
      nombre = 's' + str(i+1)
      switches_lan.append(net.addSwitch(nombre + '_lan', cls=OVSKernelSwitch, failMode='standalone'))
      switches_wan.append(net.addSwitch(nombre + '_wan', cls=OVSKernelSwitch, failMode='standalone'))

   info('*** Add routers\n')
   r_central = net.addHost('r_central', cls=Node, ip='')
   r_central.cmd('sysctl -w net.ipv4.ip_forward=1')
   
   for i in range(args.sucursales):
      routers.append(net.addHost('r' + str(i+1), cls=Node, ip=''))
      routers[i].cmd('sysctl -w net.ipv4.ip_forward=1')

   info( '*** Add hosts\n')
   for i in range(args.sucursales):
      ip = '10.0.' + str(i) + '.254/24'
      hosts.append(net.addHost('h' + str(i+1), ip=ip, defaultRoute=None))

   info( '*** Add links\n')
   for i in range(args.sucursales):
      r_central_ip = '192.168.100.' + str(6+8*i) + '/29'
      r_sucursal_ip_wan = '192.168.100.' + str(1+8*i) + '/29'
      r_sucursal_ip_lan = '10.0.' + str(i) + '.1/24'
      host_sucursal_ip = '10.0.' + str(i) + '.254/24'
      
      net.addLink(r_central, switches_wan[i], params1={'ip': r_central_ip})
      net.addLink(routers[i], switches_wan[i], params1={'ip': r_sucursal_ip_wan})
      net.addLink(routers[i], switches_lan[i], params1={'ip': r_sucursal_ip_lan})
      
      net.addLink(hosts[i], switches_lan[i], params1={'ip': host_sucursal_ip})

   info( '*** Starting network\n')
   net.build()
   info( '*** Starting controllers\n')
   for controller in net.controllers:
       controller.start()

   info( '*** Starting switches\n')
   for switch in switches_wan:
      switch.start([])
   
   for switch in switches_lan:
      switch.start([])

   info( '*** Post configure switches and hosts\n')
   
   for i in range(args.sucursales):
      net['r_central'].cmd(f"ip route add 10.0.{i}.0/24 via 192.168.100.{1+8*i}")
   
   for i in range(args.sucursales):
      routers[i].cmd(f'ip route add 10.0.{i}.0/24 via 10.0.{i}.1')
      routers[i].cmd(f'ip route add 0/0 via 192.168.100.{6+8*i}')
   
   for i in range(args.sucursales):
      hosts[i].cmd(f'ip route add 10.0.{i}.0/24 via 10.0.{i}.254')
      hosts[i].cmd(f'ip route add 0/0 via 10.0.{i}.1')

   CLI(net)
   net.stop()

if __name__ == '__main__':
   setLogLevel( 'info' )
   myNetwork()
