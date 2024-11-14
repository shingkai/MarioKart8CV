import { SERVER_CONFIG } from './config.js';
const { useState, useEffect } = React;
import { initializeRaceTracker, initializeControls } from './main.js';

const CharacterSelect = ({ value, onChange, characters }) => {  // Add characters as a prop
  const [isOpen, setIsOpen] = useState(false);

  return React.createElement('div', { className: 'relative' },
    React.createElement('button', {
      type: 'button',
      className: 'w-full bg-gray-700 text-white px-4 py-2 rounded-lg flex items-center justify-between',
      onClick: () => setIsOpen(!isOpen)
    },
      React.createElement('div', { className: 'flex items-center gap-2' },
        value ? [
          React.createElement('img', {
            key: 'char-img',
            src: `mario_kart_8_images/Character select icons/${value}.png`,
            alt: value,
            className: 'w-8 h-8 object-contain'
          }),
          React.createElement('span', { key: 'char-name' }, value)
        ] : React.createElement('span', null, 'Select Character')
      )
    ),
    isOpen && React.createElement('div', {
      className: 'absolute z-10 w-full mt-1 bg-gray-800 border border-gray-700 rounded-lg shadow-lg max-h-96 overflow-y-auto'
    }, characters.map(character =>  // Use the characters prop directly
      React.createElement('button', {
        key: character,
        type: 'button',
        className: `w-full px-4 py-2 flex items-center gap-2 hover:bg-gray-700 ${value === character ? 'bg-blue-600' : ''}`,
        onClick: () => {
          onChange(character);
          setIsOpen(false);
        }
      },
        React.createElement('img', {
          src: `mario_kart_8_images/Character select icons/${character}.png`,
          alt: character,
          className: 'w-8 h-8 object-contain'
        }),
        React.createElement('span', { className: 'text-white' }, character)
      )
    ))
  );
};

const DeviceForm = ({ characters, onSubmit }) => {
  const [formData, setFormData] = useState({
    deviceId: '',
    player1Name: '',
    player1Character: '',
    player2Name: '',
    player2Character: ''
  });

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
    setFormData({
      deviceId: '',
      player1Name: '',
      player1Character: '',
      player2Name: '',
      player2Character: ''
    });
  };

  return React.createElement('form', {
    onSubmit: handleSubmit,
    className: 'space-y-6 bg-gray-800 p-6 rounded-lg'
  },
    // Device ID
    React.createElement('div', null,
      React.createElement('label', { className: 'block text-gray-300 mb-2' }, 'Device ID'),
      React.createElement('input', {
        type: 'number',
        value: formData.deviceId,
        onChange: (e) => handleInputChange('deviceId', e.target.value),
        className: 'w-full bg-gray-700 text-white px-4 py-2 rounded-lg'
      })
    ),

    // Player 1 Section
    React.createElement('div', { className: 'space-y-4' },
      React.createElement('h3', { className: 'text-lg font-semibold text-white' }, 'Player 1 ⬅️'),
      React.createElement('div', null,
        React.createElement('label', { className: 'block text-gray-300 mb-2' }, 'Name'),
        React.createElement('input', {
          type: 'text',
          value: formData.player1Name,
          onChange: (e) => handleInputChange('player1Name', e.target.value),
          className: 'w-full bg-gray-700 text-white px-4 py-2 rounded-lg'
        })
      ),
      React.createElement('div', null,
        React.createElement('label', { className: 'block text-gray-300 mb-2' }, 'Character'),
        React.createElement(CharacterSelect, {
          value: formData.player1Character,
          onChange: (char) => handleInputChange('player1Character', char),
          characters: characters  // Pass characters to CharacterSelect
        })
      )
    ),

    // Player 2 Section
    React.createElement('div', { className: 'space-y-4' },
      React.createElement('h3', { className: 'text-lg font-semibold text-white' }, 'Player 2 ➡️'),
      React.createElement('div', null,
        React.createElement('label', { className: 'block text-gray-300 mb-2' }, 'Name'),
        React.createElement('input', {
          type: 'text',
          value: formData.player2Name,
          onChange: (e) => handleInputChange('player2Name', e.target.value),
          className: 'w-full bg-gray-700 text-white px-4 py-2 rounded-lg'
        })
      ),
      React.createElement('div', null,
        React.createElement('label', { className: 'block text-gray-300 mb-2' }, 'Character'),
        React.createElement(CharacterSelect, {
          value: formData.player2Character,
          onChange: (char) => handleInputChange('player2Character', char),
          characters: characters  // Pass characters to CharacterSelect
        })
      )
    ),

    // Submit Button
    React.createElement('button', {
      type: 'submit',
      className: 'w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center justify-center gap-2'
    }, 'Save Players')
  );
};

const TabNavigation = () => {
  const [activeTab, setActiveTab] = useState('race');
  const [racerMetadata, setRacerMetadata] = useState([]);
  const [characters, setCharacters] = useState([]);
  const [isInitialized, setIsInitialized] = useState(false);

  // Fetch characters when component mounts
  useEffect(() => {
    fetchCharacters();
    fetchRacerMetadata();
  }, []);

  const fetchCharacters = async () => {
    try {
      const response = await fetch(`${SERVER_CONFIG.HTTP_URL}/api/characters`);
      if (response.ok) {
        const data = await response.json();
        setCharacters(data);
      }
    } catch (error) {
      console.error('Error fetching characters:', error);
    }
  };

  const handleSubmit = async (formData) => {
    try {
      const response = await fetch(`${SERVER_CONFIG.HTTP_URL}/api/racer-metadata`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        fetchRacerMetadata();
      }
    } catch (error) {
      console.error('Error saving racer metadata:', error);
    }
  };

  const fetchRacerMetadata = async () => {
    try {
      const response = await fetch(`${SERVER_CONFIG.HTTP_URL}/api/racer-metadata`);
      if (response.ok) {
        const data = await response.json();
        setRacerMetadata(data);
      }
    } catch (error) {
      console.error('Error fetching racer metadata:', error);
    }
  };

  // Initialize race tracker components
  useEffect(() => {
    if (activeTab === 'race' && !isInitialized) {
      initializeRaceTracker('race-tracker');
      initializeControls('controls');
      setIsInitialized(true);
    }
    return () => {
      if (activeTab !== 'race' && isInitialized) {
        const raceTracker = document.getElementById('race-tracker');
        const controls = document.getElementById('controls');
        if (raceTracker) raceTracker.innerHTML = '';
        if (controls) controls.innerHTML = '';
        setIsInitialized(false);
      }
    };
  }, [activeTab, isInitialized]);

  return React.createElement('div', { className: 'w-full max-w-6xl mx-auto p-4' },
    // Tab buttons
    React.createElement('div', { className: 'flex space-x-2 mb-4' },
      React.createElement('button', {
        className: `px-4 py-2 rounded-lg ${activeTab === 'race' ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'}`,
        onClick: () => setActiveTab('race')
      }, 'Race Tracker'),
      React.createElement('button', {
        className: `px-4 py-2 rounded-lg ${activeTab === 'metadata' ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'}`,
        onClick: () => setActiveTab('metadata')
      }, 'Racer Metadata')
    ),

    // Tab content
    activeTab === 'race' ?
      React.createElement('div', null,
        React.createElement('div', {
          id: 'controls',
          className: 'controls',
          key: 'controls'
        }),
        React.createElement('div', {
          id: 'race-tracker',
          className: 'race-tracker',
          key: 'race-tracker'
        })
      ) :
      React.createElement('div', { className: 'space-y-6' },
        // Device Form
        React.createElement(DeviceForm, {
          characters: characters,
          onSubmit: handleSubmit
        }),

        // Racer Table
        React.createElement('div', { className: 'bg-gray-800 rounded-lg p-6' },
          React.createElement('table', { className: 'w-full text-gray-300' },
            React.createElement('thead', null,
              React.createElement('tr', { className: 'bg-gray-700' },
                ['Device ID', 'Player #', 'Player Name', 'Character'].map(header =>
                  React.createElement('th', {
                    key: header,
                    className: 'p-2 text-left'
                  }, header)
                )
              )
            ),
            React.createElement('tbody', null,
              racerMetadata.map(racer =>
                React.createElement('tr', {
                  key: `${racer.device_id}-${racer.device_player_num}`,
                  className: 'border-t border-gray-700'
                },
                  React.createElement('td', { className: 'p-2' }, racer.device_id),
                  React.createElement('td', { className: 'p-2' }, racer.device_player_num === 1 ? '1 ⬅️' : '2 ➡️'),
                  React.createElement('td', { className: 'p-2' }, racer.player_name),
                  React.createElement('td', { className: 'p-2' },
                    React.createElement('div', { className: 'flex items-center gap-2' },
                      React.createElement('img', {
                        src: `mario_kart_8_images/Character select icons/${racer.character}.png`,
                        alt: racer.character,
                        className: 'w-6 h-6 object-contain'
                      }),
                      racer.character
                    )
                  )
                )
              )
            )
          )
        )
      )
  );
};

export default TabNavigation;