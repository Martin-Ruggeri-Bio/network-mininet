from mininet.net import Mininet
from mininet.node import OVSKernelSwitch, Node
from mininet.cli import CLI
from mininet.log import info

def create_network(num_branches):
    net = Mininet(topo=None, build=False, ipBase='10.0.0.0/8')
    central_router, routers, lan_switches, wan_switches, hosts = add_elements(net, num_branches)
    add_links(net, central_router, routers, lan_switches, wan_switches, hosts, num_branches)
    start_network(net, num_branches)
    test_conexion(net, num_branches)

def add_elements(net, num_branches):
    lan_switches = []
    wan_switches = []
    routers = []
    hosts = []

    info('*** Adding switches and hosts\n')
    for i in range(num_branches):
        branch_name = 'branch' + str(i+1)
        lan_switches.append(net.addSwitch(branch_name + '_lan', cls=OVSKernelSwitch, failMode='standalone'))
        wan_switches.append(net.addSwitch(branch_name + '_wan', cls=OVSKernelSwitch, failMode='standalone'))
        lan_ip = '10.0.' + str(i+1) + '.254/24'
        hosts.append(net.addHost('host' + str(i+1), ip=lan_ip, defaultRoute=None))
        routers.append(net.addHost('router' + str(i+1), cls=Node, ip=''))
        routers[i].cmd('sysctl -w net.ipv4.ip_forward=1')

    central_router = net.addHost('central_router', cls=Node, ip='')
    central_router.cmd('sysctl -w net.ipv4.ip_forward=1')

    return central_router, routers, lan_switches, wan_switches, hosts

def add_links(net, central_router, routers, lan_switches, wan_switches, hosts, num_branches):
    info('*** Adding links\n')
    for i in range(num_branches):
        central_router_ip = '192.168.100.' + str(6 + 8*i) + '/29'
        branch_router_ip_wan = '192.168.100.' + str(1 + 8*i) + '/29'
        branch_router_ip_lan = '10.0.' + str(i+1) + '.1/24'
        host_branch_ip = '10.0.' + str(i+1) + '.254/24'

        net.addLink(central_router, wan_switches[i], params1={'ip': central_router_ip})
        net.addLink(routers[i], wan_switches[i], params1={'ip': branch_router_ip_wan})
        net.addLink(routers[i], lan_switches[i], params1={'ip': branch_router_ip_lan})
        net.addLink(hosts[i], lan_switches[i], params1={'ip': host_branch_ip})

def start_network(net, num_branches):
    info('*** Starting network\n')
    net.build()
    info('*** Starting controllers and switches\n')
    for controller in net.controllers:
        controller.start()

    for switch in net.switches:
        switch.start([])

    info('***Configure ROUTING TABLES\n')

    for i in range(num_branches):
        net['central_router'].cmd("ip route add 10.0.{0}.0/24 via 192.168.100.{1}".format(i+1, 1 + 8*i))
        net['router' + str(i+1)].cmd('ip route add 10.0.{0}.0/24 via 10.0.{0}.1'.format(i+1))
        net['router' + str(i+1)].cmd('ip route add 0/0 via 192.168.100.{0}'.format(6 + 8*i))
        net['host' + str(i+1)].cmd('ip route add 10.0.{0}.0/24 via 10.0.{0}.254'.format(i+1))
        net['host' + str(i+1)].cmd('ip route add 0/0 via 10.0.{0}.1'.format(i+1))

    CLI(net)
    net.stop()


def test_conexion(net, num_branches):
    try:
        # test de conectividad por cada branch
        for i in range(num_branches):
            # test ping router central con los routers de las sucursales
            info(net['central_router'].cmd('ping -c 1 192.168.100.{0}'.format(1 + 8*i)))
            # test ping router central con los hosts de las sucursales
            info(net['central_router'].cmd('ping -c 1 10.0.{0}.254'.format(i+1)))
            # test ping router sucursal con los hosts de la sucursal
            info(net['router' + str(i+1)].cmd('ping -c 1 10.0.{0}.254'.format(i+1)))
            # test ping router sucursal con otros routers de las sucursales
            for j in range(num_branches):
                if j != i:
                    info(net['router' + str(i+1)].cmd('ping -c 1 10.0.{0}.1'.format(j+1)))
            # test ping host sucursal con otros hosts de las sucursales
            for j in range(num_branches):
                if j != i:
                    info(net['host' + str(i+1)].cmd('ping -c 1 10.0.{0}.254'.format(j+1)))
    except Exception as e:
        print(e)


def main():
    create_network(6)

if __name__ == '__main__':
    main()
