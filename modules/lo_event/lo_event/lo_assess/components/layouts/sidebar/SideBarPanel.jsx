import React from 'react';

export function SideBarPanel({children}) {
  const childArray = React.Children.toArray(children);

  return (
    <div className="pane-with-sidebar">
      <div className="main-pane">
        { childArray[0] }
      </div>

      <div className="sidebar">
        {childArray.slice(1).map((card, index) => (
          <div className="sidebar-card" key={index}>
            {card}
          </div>
        ))}
      </div>
    </div>);
}
