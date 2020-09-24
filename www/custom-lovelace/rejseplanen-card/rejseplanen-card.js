class RejseplanenCard extends HTMLElement {
  set hass(hass) {
    const entityId = this.config.entity;
    const state = hass.states[entityId];
    const max_entries = this.config.max_entries;
    const show_scheduled_time = this.config.show_scheduled_time;

    if (state === undefined) {
      this.innerHTML = `
        <ha-card>
          <div style="display: block; color: black; background-color: #fce588; padding: 8px;">
            Entity not found: ${entityId}
          </div>
        </ha-card>
      `;
      return;
    }

    const name = this.config.title || state.attributes['friendly_name'];

    if (!this.content) {
      const card = document.createElement('ha-card');
      if (name == ' ') {
        card.header = '';
      } else {
        card.header = name;
      }
      this.content = document.createElement('div');
      const style = document.createElement('style');
      style.textContent = `
        .type-custom-rejseplanen-card table {
          width: 100%;
          padding: 6px 10px;
        }
        .type-custom-rejseplanen-card tr:nth-child(even) {
          background: var(--table-row-background-color);
        }
        .type-custom-rejseplanen-card tr:nth-child(odd) {
          background: var(--table-row-alternative-background-color);
        }
        .type-custom-rejseplanen-card td {
          padding: 3px 0px;
        }
        .type-custom-rejseplanen-card td.shrink {
          white-space:nowrap;
          padding: 0px 4px;
        }
        .type-custom-rejseplanen-card td.expand {
          width: 99%;
          padding-left: 4px;
        }
        .type-custom-rejseplanen-card span.route {
          font-weight: bold;
          font-size:0.9em;
          padding:3px 8px 2px 8px;
          color: #fff;
          background-color: #888;
          margin-right:0.7em;
          border-radius: 2px;
        }
        .type-custom-rejseplanen-card span.track {
          color: var(--secondary-text-color);
          font-size: 90%;
          float: right;
          padding-right: 4px;
        }
        .type-custom-rejseplanen-card span.delay {
          color: #b41730;
          font-size: 90%;
          float: right;
          padding-right: 4px;
        }

        .type-custom-rejseplanen-card span.type-S.route-A {
          background-color: #4AA5E5;
        }

        .type-custom-rejseplanen-card span.type-S.route-B {
          background-color: #68AB45;
        }

        .type-custom-rejseplanen-card span.type-S.route-Bx {
          background-color: #B3CD78;
        }

        .type-custom-rejseplanen-card span.type-S.route-C {
          background-color: #E59535;
        }

        .type-custom-rejseplanen-card span.type-S.route-E {
          background-color: #7670B3;
        }

        .type-custom-rejseplanen-card span.type-S.route-F {
          background-color: #F4C443;
        }

        .type-custom-rejseplanen-card span.type-S.route-H {
          background-color: #D44E28;
        }

        .type-custom-rejseplanen-card span.type-M.route-Metro-M1 {
          background-color: #037756;
        }

        .type-custom-rejseplanen-card span.type-M.route-Metro-M2 {
          background-color: #FECE00;
        }

        .type-custom-rejseplanen-card span.type-M.route-Metro-M3 {
          background-color: #EA3755;
        }

        .type-custom-rejseplanen-card span.type-M.route-Metro-M4 {
          background-color: #3CB4EF;
        }

        .type-custom-rejseplanen-card span.type-REG {
          background-color: #47A541;
        }

        .type-custom-rejseplanen-card span.type-IC {
          background-color: #EE4230;
        }

        .type-custom-rejseplanen-card span.type-LYN {
          background-color: #FCBB58;
        }

        .type-custom-rejseplanen-card span.type-TOG[class*=" route-SJ"] {
          background-color: #767676;
        }

        .type-custom-rejseplanen-card span.type-TOG[class*=" route-Lokalbane"] {
          background-color: #061D42;
        }

        .type-custom-rejseplanen-card span[class*=" route-Letbane-"] {
          background-color: #31546F;
        }

        .type-custom-rejseplanen-card span.type-BUS {
          background-color: #FEC100;
        }

        .type-custom-rejseplanen-card span.type-EXB {
          background-color: #2A8DFF;
        }

        .type-custom-rejseplanen-card span[class*=" route-Bus-"][class$="A"] {
          background-color: #B12222;
        }

        .type-custom-rejseplanen-card span[class*=" route-Bus-"][class$="C"] {
          background-color: #17AACF;
        }

        .type-custom-rejseplanen-card span[class*=" route-Bus-"][class$="E"] {
          background-color: #228C22;
        }

        .type-custom-rejseplanen-card span[class*=" route-Bus-"][class$="N"] {
          background-color: #808080;
        }

        .type-custom-rejseplanen-card span[class*=" route-Havnebus-"] {
          background-color: #021C4C;
        }
        `;
      card.appendChild(style);
      card.appendChild(this.content);
      this.appendChild(card);
    }

    var tablehtml = `
    <table>
    `;

    var journeys = [];
    if (state.state != 'unknown') {
      const next = {
        'route': state.attributes['route'],
        'type': state.attributes['type'],
        'due_in': state.attributes['due_in'],
        'scheduled_at': state.attributes['scheduled_at'],
        'direction': state.attributes['direction'],
        'track': state.attributes['track'],
        'real_time_at': state.attributes['real_time_at'],
      };

      journeys = [next].concat(state.attributes['next_departures']);
    }

    if (max_entries) {
      journeys = journeys.slice(0, max_entries);
    }

    for (const journey of journeys) {
      const direction = journey['direction'];
      const routename = journey['route'];
      const type = journey['type'];
      const track = journey['track'];
      const realTimeAt = journey['real_time_at'];
      let time = journey['due_in'];

      if (show_scheduled_time) {
        time = journey['scheduled_at'].split(' ')[1]
      }

      const styleType = type.replace(' ', '-');
      const styleRoutename = routename.replace(' ', '-');

      let trackSnippet = '';
      if (track) {
        trackSnippet = `<span class="track">Spor ${track}</span>`;
      }

      let delaySnippet = '';
      if (realTimeAt) {
        const realTimeAtTime = realTimeAt.split(' ')[1]
        delaySnippet = `<span class="delay">(${realTimeAtTime})</span>`
      }

      tablehtml += `
          <tr>
            <td class="shrink" style="text-align:center;"><span class="route type-${styleType} route-${styleRoutename}">${routename}</span></td>
            <td class="expand">
              ${direction}
              ${delaySnippet}
              ${trackSnippet}
            </td>
            <td class="shrink" style="text-align:right;">${time}</td>
          </tr>
      `;
    }
    tablehtml += `
    </table>
    `;

    this.content.innerHTML = tablehtml;
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error('You need to define an entity');
    }
    this.config = config;
  }

  getCardSize() {
    return 1
  }
}

customElements.define('rejseplanen-card', RejseplanenCard);
