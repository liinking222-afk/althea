// pipe.js - Compose single-purpose functions left-to-right
// Each function does ONE thing. Names are documentation. Chain with pipes.

const pipe = (...fns) => input => fns.reduce((acc, fn) => fn(acc), input);

const compose = (...fns) => input => fns.reduceRight((acc, fn) => fn(acc), input);

const tap = fn => input => { fn(input); return input; };

const map = fn => arr => arr.map(fn);

const filter = pred => arr => arr.filter(pred);

const reduce = (fn, init) => arr => arr.reduce(fn, init);

const head = arr => arr[0];

const tail = arr => arr.slice(1);

const take = n => arr => arr.slice(0, n);

const prop = key => obj => obj[key];

const pluck = key => arr => arr.map(obj => obj[key]);

const identity = x => x;

const constant = x => () => x;

const trace = label => tap(x => console.log(`[${label}]`, x));

module.exports = {
  pipe,
  compose,
  tap,
  map,
  filter,
  reduce,
  head,
  tail,
  take,
  prop,
  pluck,
  identity,
  constant,
  trace
};