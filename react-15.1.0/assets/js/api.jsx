import React from 'react';

import Menu from 'material-ui/Menu';
import MenuItem from 'material-ui/MenuItem';
import Paper from 'material-ui/Paper';
import {
  Table, TableBody, TableHeader, TableHeaderColumn, TableRow, TableRowColumn
} from 'material-ui/Table';


/*
const client = new $.RestClient('http://localhost:8991/api/');
client.add('devices');
*/

const URL = 'http://localhost:8991/api/';

class Api {
  constructor(url=URL) {
    var client = new $.RestClient(url);

    //
    //  Here we're setting up endpoints for all of the NSoT API resources.
    //

    // Sites
    this.sites = client.add('sites');

    // Attributes
    this.attributes = client.add('attributes');

    // Changes
    this.changes = client.add('changes');

    // Devices 
    this.devices = client.add('devices');
    this.devices.query = client.add(
      'devices_query', {url: 'devices/query'}
    );
    this.devices.add('interfaces');

    // Interfaces
    this.interfaces = client.add('interfaces');
    this.interfaces.query = client.add(
      'interfaces_query', {url: 'interfaces/query'}
    );
    this.interfaces.add('addresses');
    this.interfaces.add('assignments');
    this.interfaces.add('networks');

    // Networks
    this.networks = client.add('networks');
    this.networks.query = client.add(
      'networks_query', {url: 'networks/query'}
    );
    this.networks.reserved = client.add(
      'networks_reserved', {url: 'networks/reserved'}
    );
    this.networks.add('ancestors');
    this.networks.add('assignments');
    this.networks.add('children');
    this.networks.add('closest_parent');
    this.networks.add('descendents');
    this.networks.add('next_address');
    this.networks.add('next_network');
    this.networks.add('parent_', {url: 'parent'});  // Parent collides w/ client
    this.networks.add('root_', {url: 'root'});  // Root collides w/ client
    this.networks.add('siblings');
    this.networks.add('subnets');
    this.networks.add('supernets');

    // Users
    this.users = client.add('users');
    this.users.add('rotate_secret_key');

    // Values
    this.values = client.add('values');

    // Store the core client on the object.
    this.client = client;
  }

}
// document.Api = Api;

export default Api;


/*
class Network extends Api {
  constructor(url) {
    super(url);
    // this.client.networks.add('children');
    // this.networks.children = this.client.networks.add('children');
  }

}
document.Network = Network;
*/
