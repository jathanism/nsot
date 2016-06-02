import React from 'react';

class ResourceLayout extends React.Component {
  render() {
    return (
      <div>
        {this.props.children}
      </div>
    );
  }
}

export default ResourceLayout;
