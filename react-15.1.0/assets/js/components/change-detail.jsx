import React from 'react';
import Api from '../api';

const client = new Api();

class ChangeDetail extends React.Component {
  render() {
    return (
      <div>
        <h1>{this.props.change.hostname}</h1>
        Change detail for id: {this.props.change.id}
      </div>
    );
  }
}

// export default ChangeDetail;


class ChangeDetailContainer extends React.Component {
  constructor(props) {
    super(props);
    this.state = {change: {}};
  }

  componentDidMount() {
    console.log(this.props.params);
    var request = client.changes.read(this.props.params.changeId);
    var response = request.done((data, textStatus, xhrObject) => {
        console.log(data);
        this.setState({change: data});
      }
    );

  }

  render() {
    return (
      <ChangeDetail change={this.state.change} />
    );
  }
}

export default ChangeDetailContainer;
