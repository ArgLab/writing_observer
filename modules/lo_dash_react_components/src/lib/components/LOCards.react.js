/*
  Unfinished code. Committing to branch to sync.
  */

import React from "react";
import "./LOCards.css";

const LOCard = ({ title, description }) => {
  return (
    <div className="lo-card">
      <h2>{title}</h2>
      <p>{description}</p>
    </div>
  );
};

const LOFlow = ({ children }) => {
  const cards = React.Children.toArray(children);

  return (
    <div className="flow">
      {cards.map((card, index) => (
        <React.Fragment key={index}>
          {card}
          {index < cards.length - 1 && <div className="arrow" />}
        </React.Fragment>
      ))}
    </div>
  );
};

const App = () => {
  return (
    <div className="app">
      <LOFlow>
        <LOCard title="Card 1" description="Description of card 1" />
        <LOCard title="Card 2" description="Description of card 2" />
        <LOCard title="Card 3" description="Description of card 3" />
      </LOFlow>
    </div>
  );
};

export default App;
