/*jshint esversion: 9 */
class RejseplanenStogCard extends HTMLElement {
  set hass(hass) {
    const entityId = this.config.entity;
    const max_entries = this.config.max_entries;
    const state = hass.states[entityId];

    if (state === undefined) {
      this.innerHTML = `
        <style>
          .warning {
            display: block;
            color: black;
            background-color: #fce588;
            padding: 8px;
          }
        </style>
        <ha-card>
          <div class="warning">Entity not found: ${entityId} </div>
        </ha-card>
      `;
      return;
    }

    const name = this.config.title || state.attributes["friendly_name"];

    if (!this.content) {
      const card = document.createElement("ha-card");
      if (name == " ") {
        card.header = "";
      } else {
        card.header = name;
      }
      this.content = document.createElement("div");
      const style = document.createElement("style");
      style.textContent = `
        rejseplanen-stog-card  {
          font-family: sans-serif;
          font-weight: bold;
        }
        rejseplanen-stog-card .card-header  {
          padding: 16px 16px 4px 16px;
        }
        rejseplanen-stog-card table {
          width: 100%;
          padding: 0px 10px;
          font-size: 150%;

          border-collapse:separate; 
          border-spacing:0 16px;
        }
        rejseplanen-stog-card tr {
          background: none;
          border-spacing: 10px 0
        }
        rejseplanen-stog-card td {
          background: none;
          padding: 8px 0 6px 0;
        }
        rejseplanen-stog-card td.shrink {
          white-space:nowrap;
        }
        rejseplanen-stog-card td.expand {
          width: 99%;
        }
        rejseplanen-stog-card td.time {
          padding: 8px 16px 0 0;
        }
        rejseplanen-stog-card td.direction {
          background: var(--table-row-background-color);
          box-shadow: -2px 2px 0px 1px rgba(0,0,0,0.25), 1px -1px 0px 0px rgba(255,255,255,0.25);
        }
        rejseplanen-stog-card span.route {
          color: #fff;
          background-color: #888;
          padding: 8px 6px 5px 6px;
        }
        rejseplanen-stog-card span.delay {
          padding-right: 4px;
          float: right;
          font-size: 66%;
          color: #b41730;
        }
        rejseplanen-stog-card td.track {
          padding: 8px 0 0 16px;
        }
        rejseplanen-stog-card td.track span {
          font-size: 50%;
        }
        rejseplanen-stog-card td.time span {
          font-size: 50%;
        }

        rejseplanen-stog-card span.type-S.route-A {
          background-color: #4AA5E5;
        }

        rejseplanen-stog-card span.type-S.route-B {
          background-color: #68AB45;
        }

        rejseplanen-stog-card span.type-S.route-Bx {
          background-color: #B3CD78;
        }

        rejseplanen-stog-card span.type-S.route-C {
          background-color: #E59535;
        }

        rejseplanen-stog-card span.type-S.route-E {
          background-color: #7670B3;
        }

        rejseplanen-stog-card span.type-S.route-F {
          background-color: #F4C443;
        }

        rejseplanen-stog-card span.type-S.route-H {
          background-color: #D44E28;
        }

        rejseplanen-stog-card span.type-M.route-Metro-M1 {
          background-color: #037756;
        }

        rejseplanen-stog-card span.type-M.route-Metro-M2 {
          background-color: #FECE00;
        }

        rejseplanen-stog-card span.type-M.route-Metro-M3 {
          background-color: #EA3755;
        }

        rejseplanen-stog-card span.type-M.route-Metro-M4 {
          background-color: #3CB4EF;
        }

        rejseplanen-stog-card span.type-REG {
          background-color: #47A541;
        }

        rejseplanen-stog-card span.type-IC {
          background-color: #EE4230;
        }

        rejseplanen-stog-card span.type-LYN {
          background-color: #FCBB58;
        }

        rejseplanen-stog-card span.type-TOG[class*=" route-SJ"] {
          background-color: #767676;
        }

        rejseplanen-stog-card span.type-TOG[class*=" route-Lokalbane"] {
          background-color: #061D42;
        }

        rejseplanen-stog-card span[class*=" route-Letbane-"] {
          background-color: #31546F;
        }

        rejseplanen-stog-card span.type-BUS {
          background-color: #FEC100;
        }

        rejseplanen-stog-card span.type-EXB {
          background-color: #2A8DFF;
        }

        rejseplanen-stog-card span[class*=" route-Bus-"][class$="A"] {
          background-color: #B12222;
        }

        rejseplanen-stog-card span[class*=" route-Bus-"][class$="C"] {
          background-color: #17AACF;
        }

        rejseplanen-stog-card span[class*=" route-Bus-"][class$="E"] {
          background-color: #228C22;
        }

        rejseplanen-stog-card span[class*=" route-Bus-"][class$="N"] {
          background-color: #808080;
        }

        rejseplanen-stog-card span[class*=" route-Havnebus-"] {
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
    if (state.state != "unknown") {
      const next = {
        route: state.attributes["route"],
        type: state.attributes["type"],
        due_in: state.attributes["due_in"],
        direction: state.attributes["direction"],
        track: state.attributes["track"],
        real_time_at: state.attributes["real_time_at"],
      };

      journeys = [next].concat(state.attributes["next_departures"]);
    }

    if (max_entries) {
      journeys = journeys.slice(0, max_entries);
    } else {
      journeys = journeys.slice(0, 2);
    }

    for (const journey of journeys) {
      const direction = journey["direction"];
      const routename = journey["route"];
      const type = journey["type"];
      const time = journey["due_in"];
      const track = journey["track"];
      const realTimeAt = journey["real_time_at"];

      const styleType = type.replace(" ", "-");
      const styleRoutename = routename.replace(" ", "-");

      let trackSnippet = "";
      if (track) {
        trackSnippet = `<span>Spor </span>${track}`;
      }

      let delaySnippet = "";
      if (realTimeAt) {
        const realTimeAtTime = realTimeAt.split(" ")[1];
        delaySnippet = `<span class="delay">(${realTimeAtTime})</span>`;
      }

      tablehtml += `
          <tr>
            <td class="shrink time">${time}<span> min</span></td>
            <td class="expand direction">
              <span class="route type-${styleType} route-${styleRoutename}">${routename}</span>
              ${direction}
              ${delaySnippet}
            </td>
            <td class="shrink track" style="text-align:right;">${trackSnippet}</td>
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
      throw new Error("You need to define an entity");
    }
    this.config = config;
  }

  getCardSize() {
    return 1;
  }
}

customElements.define("rejseplanen-stog-card", RejseplanenStogCard);
