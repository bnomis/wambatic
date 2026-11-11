(function () {
  'use strict';

  var collator = new Intl.Collator(undefined, { numeric: true, sensitivity: 'base' });
  var NUMBER = '[+-]?(?:\\d+\\.?\\d*|\\.\\d+)';
  var COMPARE = new RegExp('^(>=|<=|=|>|<)?\\s*(' + NUMBER + ')$');
  var RANGE = new RegExp('^(' + NUMBER + ')\\s*\\.\\.\\s*(' + NUMBER + ')$');

  function numberTest(input) {
    var text = input.replace(/[,%]/g, '').trim();
    var range = RANGE.exec(text);
    if (range) {
      var low = Number(range[1]);
      var high = Number(range[2]);
      return function (value) {
        return value >= low && value <= high;
      };
    }
    var compare = COMPARE.exec(text);
    if (!compare) {
      return null;
    }
    var limit = Number(compare[2]);
    var tests = {
      '>=': function (value) { return value >= limit; },
      '<=': function (value) { return value <= limit; },
      '>': function (value) { return value > limit; },
      '<': function (value) { return value < limit; },
      '=': function (value) { return value === limit; }
    };
    return tests[compare[1] || '='];
  }

  function cellValue(row, column) {
    var raw = row.cells[column].getAttribute('data-value');
    return raw === null || raw === '' ? null : Number(raw);
  }

  function count(value) {
    return value.toLocaleString('en-US');
  }

  function enhance(table) {
    var head = table.tHead.rows[0];
    var body = table.tBodies[0];
    var foot = table.tFoot ? table.tFoot.rows[0] : null;
    var types = Array.prototype.map.call(head.cells, function (cell) {
      return cell.getAttribute('data-type');
    });
    var original = Array.prototype.slice.call(body.rows);
    var position = new Map(original.map(function (row, index) { return [row, index]; }));
    var sort = { column: -1, direction: 'none' };
    var footLabel = foot ? foot.cells[0].textContent : '';
    var filters = [];
    var timer = null;

    var status = document.createElement('p');
    status.className = 'table-status';
    status.setAttribute('role', 'status');
    table.insertAdjacentElement('afterend', status);

    var filterRow = document.createElement('tr');
    filterRow.className = 'filters';

    function order() {
      var sorted = original.slice();
      if (sort.column >= 0) {
        var column = sort.column;
        var sign = sort.direction === 'ascending' ? 1 : -1;
        var numeric = types[column] === 'number';
        sorted.sort(function (a, b) {
          var result;
          if (numeric) {
            var x = cellValue(a, column);
            var y = cellValue(b, column);
            if (x === null || y === null) {
              if (x === y) {
                return position.get(a) - position.get(b);
              }
              return x === null ? 1 : -1;
            }
            result = (x - y) * sign;
          } else {
            result = collator.compare(
              a.cells[column].textContent, b.cells[column].textContent
            ) * sign;
          }
          return result || position.get(a) - position.get(b);
        });
      }
      sorted.forEach(function (row) {
        body.appendChild(row);
      });
    }

    function apply() {
      var tests = [];
      var active = false;
      filters.forEach(function (input, column) {
        var text = input.value.trim();
        input.removeAttribute('aria-invalid');
        if (!text) {
          return;
        }
        if (types[column] === 'number') {
          var test = numberTest(text);
          if (!test) {
            input.setAttribute('aria-invalid', 'true');
            return;
          }
          active = true;
          tests.push(function (row) {
            var value = cellValue(row, column);
            return value !== null && test(value);
          });
        } else {
          var needle = text.toLowerCase();
          active = true;
          tests.push(function (row) {
            return row.cells[column].textContent.toLowerCase().indexOf(needle) >= 0;
          });
        }
      });
      var shown = 0;
      original.forEach(function (row) {
        var keep = tests.every(function (test) { return test(row); });
        row.hidden = !keep;
        if (keep) {
          shown += 1;
        }
      });
      if (foot) {
        foot.cells[0].textContent = active ? 'Total (all rows)' : footLabel;
      }
      status.textContent = 'Showing ' + count(shown) + ' of ' + count(original.length) + ' rows';
    }

    Array.prototype.forEach.call(head.cells, function (cell, column) {
      var label = cell.textContent;
      var button = document.createElement('button');
      button.type = 'button';
      button.className = 'sort';
      var arrow = document.createElement('span');
      arrow.className = 'arrow';
      arrow.setAttribute('aria-hidden', 'true');
      button.appendChild(document.createTextNode(label));
      button.appendChild(arrow);
      cell.textContent = '';
      cell.appendChild(button);
      cell.setAttribute('aria-sort', 'none');
      button.addEventListener('click', function () {
        var same = sort.column === column;
        var next = 'ascending';
        if (same && sort.direction === 'ascending') {
          next = 'descending';
        } else if (same && sort.direction === 'descending') {
          next = 'none';
        }
        sort = { column: next === 'none' ? -1 : column, direction: next };
        Array.prototype.forEach.call(head.cells, function (other, index) {
          var on = index === column && next !== 'none';
          other.setAttribute('aria-sort', on ? next : 'none');
          other.querySelector('.arrow').textContent =
            on ? (next === 'ascending' ? '▲' : '▼') : '';
        });
        order();
      });

      var filterCell = document.createElement('th');
      var input = document.createElement('input');
      input.type = 'text';
      input.setAttribute('aria-label', 'Filter ' + label);
      input.addEventListener('input', function () {
        clearTimeout(timer);
        timer = setTimeout(apply, 150);
      });
      filterCell.appendChild(input);
      filterRow.appendChild(filterCell);
      filters.push(input);
    });
    head.parentNode.appendChild(filterRow);
    apply();
  }

  document.querySelectorAll('.table-block table').forEach(enhance);
})();
