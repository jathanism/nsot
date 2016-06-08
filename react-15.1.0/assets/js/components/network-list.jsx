import React from 'react';
import {Link} from 'react-router';

import Menu from 'material-ui/Menu';
import MenuItem from 'material-ui/MenuItem';
import Paper from 'material-ui/Paper';
import {
  Table, TableBody, TableHeader, TableHeaderColumn, TableRow, TableRowColumn
} from 'material-ui/Table';

import Api from '../api';


const client = new Api();


// Displays an attribute as "<b>key</b>: value"
class Attribute extends React.Component {
  render() {
    return (
      <div className="attribute">
        <b>{this.props.name}:</b> {this.props.value}
      </div>
    )
  }
}


// Displays an object's attributes in a list
class AttributeList extends React.Component {
  render() {
    var attrs = [];
    var attr_id = 0;

    for (var attr in this.props.attributes) {
      attrs.push(
        <Attribute 
          name={attr}
          value={this.props.attributes[attr]}
          key={attr + attr_id}
        />
      );
      attr_id++;
    };

    return (
      <div className="attributes">
        {attrs}
      </div>
    )
  }
}


// Displays a Network by hostname followed by its attributes
class Network extends React.Component {
  render() {
    var network = this.props.network
    var cidr = `${network.network_address}/${network.prefix_length}`

    return (
      <TableRow>
        <TableRowColumn>
          <Link to={'/networks/' + this.props.network.id}>
            {cidr}
          </Link>
        </TableRowColumn>
        <TableRowColumn>
          <AttributeList attributes={this.props.network.attributes} />
        </TableRowColumn>
      </TableRow>
    );
  }
}


// Displays a list of Networks
class NetworkList extends React.Component {
  render() {
    return (
      <Table>
        <TableHeader displaySelectAll={false}>
          <TableRow>
            <TableHeaderColumn>CIDR</TableHeaderColumn>
            <TableHeaderColumn>Attributes</TableHeaderColumn>
          </TableRow>
        </TableHeader>
        <TableBody>
          {this.props.networks.map(this.createTableRow)}
        </TableBody>
      </Table>
    );
  }

  createTableRow(network) {
    return (
      <Network network={network} key={network.id} />
    );
  }
}

export default NetworkList;

class NetworkListContainer extends React.Component {
  constructor(props) {
    super(props);
    this.state = {networks: []};
  }

  // Load the networks and store them as a state object once the response is
  // ready.
  componentDidMount() {
    var request = client.networks.read();
    var response = request.done((data, textStatus, xhrObject) => {
        console.log(data);
        this.setState({networks: data});
      }
    );

  }

  render() {
    return (
      <NetworkList networks={this.state.networks} />
    );
  }

}

export default NetworkListContainer;
