(function () {
  'use strict';

  var data = JSON.parse(document.getElementById('wambatic-data').textContent);
  var root = document.documentElement;
  var dark = window.matchMedia('(prefers-color-scheme: dark)');
  var config = { responsive: true, displaylogo: false };
  var periodKeys = [];
  var shown = data.initial;

  Object.keys(data.periods).forEach(function (granularity) {
    data.periods[granularity].forEach(function (figure) {
      if (periodKeys.indexOf(figure.key) < 0) {
        periodKeys.push(figure.key);
      }
    });
  });

  function activeTheme() {
    var set = root.getAttribute('data-theme');
    if (set === 'light' || set === 'dark') {
      return set;
    }
    return dark.matches ? 'dark' : 'light';
  }

  function copy(value) {
    return JSON.parse(JSON.stringify(value));
  }

  function gradient(steps) {
    return steps.map(function (colour, index) {
      return [index / (steps.length - 1), colour];
    });
  }

  function colourTrace(trace, colours) {
    var meta = trace.meta || {};
    if (meta.slot) {
      var colour = colours.categorical[meta.slot - 1];
      trace.marker = trace.marker || {};
      trace.marker.color = colour;
      if (trace.type === 'bar') {
        trace.marker.pattern = trace.marker.pattern || {};
        trace.marker.pattern.fgcolor = colour;
      } else {
        trace.line = trace.line || {};
        trace.line.color = colour;
      }
    }
    if (meta.scale === 'sequential') {
      trace.colorscale = gradient(colours.sequential);
    }
  }

  function themed(figure, theme) {
    var colours = data.palette[theme];
    var result = copy(figure);
    var layout = result.layout;
    result.data.forEach(function (trace) {
      colourTrace(trace, colours);
    });
    layout.paper_bgcolor = colours.surface;
    layout.plot_bgcolor = colours.surface;
    layout.font = layout.font || {};
    layout.font.color = colours.ink;
    ['xaxis', 'yaxis'].forEach(function (name) {
      layout[name] = layout[name] || {};
      layout[name].gridcolor = colours.grid;
      layout[name].zerolinecolor = colours.ink_secondary;
    });
    (layout.annotations || []).forEach(function (annotation) {
      if (annotation.name === 'caption') {
        annotation.font = annotation.font || {};
        annotation.font.color = colours.ink_secondary;
      }
    });
    return result;
  }

  var panels = Array.prototype.slice.call(document.querySelectorAll('[role="tabpanel"]'));
  var drawn = {};
  var current = null;

  function draw(figure, redraw) {
    var element = document.getElementById(figure.key);
    if (!element) {
      return;
    }
    var ready = themed(figure, activeTheme());
    if (redraw) {
      Plotly.react(element, ready.data, ready.layout, config);
    } else {
      Plotly.newPlot(element, ready.data, ready.layout, config);
    }
  }

  function inPanel(panel, key) {
    var element = document.getElementById(key);
    return element && panel.contains(element);
  }

  function drawPeriods(panel, granularity, redraw) {
    var figures = {};
    data.periods[granularity].forEach(function (figure) {
      figures[figure.key] = figure;
    });
    periodKeys.forEach(function (key) {
      if (!inPanel(panel, key)) {
        return;
      }
      var element = document.getElementById(key);
      if (figures[key]) {
        element.parentElement.hidden = false;
        draw(figures[key], redraw);
      } else {
        element.parentElement.hidden = true;
      }
    });
  }

  function drawFixed(panel, redraw) {
    data.range.concat(data.calendar ? [data.calendar] : []).forEach(function (figure) {
      if (inPanel(panel, figure.key)) {
        draw(figure, redraw);
      }
    });
  }

  function drawPanel(panel) {
    var stamp = shown + '/' + activeTheme();
    var before = drawn[panel.id];
    if (before === stamp) {
      panel.querySelectorAll('.plot').forEach(function (element) {
        if (element.data) {
          Plotly.Plots.resize(element);
        }
      });
      return;
    }
    drawPeriods(panel, shown, before !== undefined);
    drawFixed(panel, before !== undefined);
    drawn[panel.id] = stamp;
  }

  function showTables(granularity) {
    document.querySelectorAll('table.period').forEach(function (table) {
      table.hidden = table.getAttribute('data-granularity') !== granularity;
    });
    document.querySelectorAll('details.table-block').forEach(function (block) {
      var table = block.querySelector('table.period:not([hidden])');
      var count = block.querySelector('.row-count');
      if (table && count) {
        var rows = table.tBodies[0].rows.length;
        count.textContent = rows.toLocaleString('en-US') + (rows === 1 ? ' row' : ' rows');
      }
    });
  }

  function buttonFor(panel) {
    return document.querySelector('[role="tab"][aria-controls="' + panel.id + '"]');
  }

  function select(panel, setFragment) {
    current = panel;
    panels.forEach(function (other) {
      var active = other === panel;
      other.hidden = !active;
      var button = buttonFor(other);
      if (button) {
        button.setAttribute('aria-selected', active ? 'true' : 'false');
        button.tabIndex = active ? 0 : -1;
      }
    });
    if (setFragment) {
      history.replaceState(null, '', '#' + panel.id);
    }
    drawPanel(panel);
  }

  function moveTab(event) {
    var index = panels.indexOf(current);
    var keys = {
      ArrowLeft: index - 1 < 0 ? panels.length - 1 : index - 1,
      ArrowRight: (index + 1) % panels.length,
      Home: 0,
      End: panels.length - 1
    };
    if (!(event.key in keys)) {
      return;
    }
    event.preventDefault();
    var target = panels[keys[event.key]];
    select(target, true);
    buttonFor(target).focus();
  }

  function startTabs() {
    var bar = document.querySelector('[role="tablist"]');
    if (!bar || !panels.length) {
      return;
    }
    bar.hidden = false;
    panels.forEach(function (panel) {
      buttonFor(panel).addEventListener('click', function () {
        select(panel, true);
      });
    });
    bar.addEventListener('keydown', moveTab);
    var named = panels.filter(function (panel) {
      return '#' + panel.id === window.location.hash;
    });
    select(named.length ? named[0] : panels[0], false);
  }

  function choose(event) {
    shown = event.target.value;
    showTables(shown);
    if (current) {
      drawPanel(current);
    }
  }

  document.querySelectorAll('input[name="granularity"]').forEach(function (radio) {
    radio.addEventListener('change', choose);
  });

  dark.addEventListener('change', function () {
    if (current) {
      drawPanel(current);
    }
  });

  showTables(shown);
  startTabs();
})();
