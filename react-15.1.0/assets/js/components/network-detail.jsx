import React from 'react';
import Api from '../api';

const client = new Api();

class NetworkDetail extends React.Component {
  render() {
    // var network = this.props.network;
    // var cidr = `${network.network_address}/${network.prefix_length}`;
    
    return (
      <div>
        <h1>{this.props.network.cidr}</h1>
        Network detail for id: {this.props.network.id}
      </div>
    );
  }
}

export default NetworkDetail;


class NetworkDetailContainer extends React.Component {
  constructor(props) {
    super(props);
    this.state = {network: {}};
  }

  componentDidMount() {
    console.log(this.props.params);
    var request = client.networks.read(this.props.params.networkId);
    var response = request.done((data, textStatus, xhrObject) => {
        console.log(data);
        data.cidr = `${data.network_address}/${data.prefix_length}`;
        this.setState({network: data});
      }
    );

  }

  render() {
    return (
      <NetworkDetail network={this.state.network} />
    );
  }
}

export default NetworkDetailContainer;
