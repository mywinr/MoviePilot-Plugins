System.register(['./__federation_fn_import-7596a93e.js'], (function (exports, module) {
  'use strict';
  var importShared;
  return {
    setters: [module => {
      importShared = module.importShared;
    }],
    execute: (async function () {

      exports({
        createVuetify: createVuetify,
        useDisplay: useDisplay,
        useLayout: useLayout,
        useLocale: useLocale,
        useRtl: useRtl,
        useTheme: useTheme
      });

      // Utilities
      await importShared('vue');


      // Types

      function getNestedValue(obj, path, fallback) {
        const last = path.length - 1;
        if (last < 0) return obj === undefined ? fallback : obj;
        for (let i = 0; i < last; i++) {
          if (obj == null) {
            return fallback;
          }
          obj = obj[path[i]];
        }
        if (obj == null) return fallback;
        return obj[path[last]] === undefined ? fallback : obj[path[last]];
      }
      function getObjectValueByPath(obj, path, fallback) {
        // credit: http://stackoverflow.com/questions/6491463/accessing-nested-javascript-objects-with-string-key#comment55278413_6491621
        if (obj == null || !path || typeof path !== 'string') return fallback;
        if (obj[path] !== undefined) return obj[path];
        path = path.replace(/\[(\w+)\]/g, '.$1'); // convert indexes to properties
        path = path.replace(/^\./, ''); // strip a leading dot
        return getNestedValue(obj, path.split('.'), fallback);
      }
      function createRange(length) {
        let start = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : 0;
        return Array.from({
          length
        }, (v, k) => start + k);
      }
      function isObject(obj) {
        return obj !== null && typeof obj === 'object' && !Array.isArray(obj);
      }
      function pick(obj, paths) {
        const found = Object.create(null);
        const rest = Object.create(null);
        for (const key in obj) {
          if (paths.some(path => path instanceof RegExp ? path.test(key) : path === key)) {
            found[key] = obj[key];
          } else {
            rest[key] = obj[key];
          }
        }
        return [found, rest];
      }
      function clamp(value) {
        let min = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : 0;
        let max = arguments.length > 2 && arguments[2] !== undefined ? arguments[2] : 1;
        return Math.max(min, Math.min(max, value));
      }
      function padEnd(str, length) {
        let char = arguments.length > 2 && arguments[2] !== undefined ? arguments[2] : '0';
        return str + char.repeat(Math.max(0, length - str.length));
      }
      function chunk(str) {
        let size = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : 1;
        const chunked = [];
        let index = 0;
        while (index < str.length) {
          chunked.push(str.substr(index, size));
          index += size;
        }
        return chunked;
      }
      function mergeDeep() {
        let source = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : {};
        let target = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : {};
        let arrayFn = arguments.length > 2 ? arguments[2] : undefined;
        const out = {};
        for (const key in source) {
          out[key] = source[key];
        }
        for (const key in target) {
          const sourceProperty = source[key];
          const targetProperty = target[key];

          // Only continue deep merging if
          // both properties are objects
          if (isObject(sourceProperty) && isObject(targetProperty)) {
            out[key] = mergeDeep(sourceProperty, targetProperty, arrayFn);
            continue;
          }
          if (Array.isArray(sourceProperty) && Array.isArray(targetProperty) && arrayFn) {
            out[key] = arrayFn(sourceProperty, targetProperty);
            continue;
          }
          out[key] = targetProperty;
        }
        return out;
      }
      function toKebabCase() {
        let str = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : '';
        if (toKebabCase.cache.has(str)) return toKebabCase.cache.get(str);
        const kebab = str.replace(/[^a-z]/gi, '-').replace(/\B([A-Z])/g, '-$1').toLowerCase();
        toKebabCase.cache.set(str, kebab);
        return kebab;
      }
      toKebabCase.cache = new Map();

      /* eslint-disable no-console */
      // import Vuetify from '../framework'

      function createMessage(message, vm, parent) {
        // if (Vuetify.config.silent) return

        if (parent) {
          vm = {
            __isVue: true,
            $parent: parent,
            $options: vm
          };
        }
        if (vm) {
          // Only show each message once per instance
          vm.$_alreadyWarned = vm.$_alreadyWarned || [];
          if (vm.$_alreadyWarned.includes(message)) return;
          vm.$_alreadyWarned.push(message);
        }
        return `[Vuetify] ${message}` + (vm ? generateComponentTrace(vm) : '');
      }
      function consoleWarn(message, vm, parent) {
        const newMessage = createMessage(message, vm, parent);
        newMessage != null && console.warn(newMessage);
      }
      function consoleError(message, vm, parent) {
        const newMessage = createMessage(message, vm, parent);
        newMessage != null && console.error(newMessage);
      }

      /**
       * Shamelessly stolen from vuejs/vue/blob/dev/src/core/util/debug.js
       */

      const classifyRE = /(?:^|[-_])(\w)/g;
      const classify = str => str.replace(classifyRE, c => c.toUpperCase()).replace(/[-_]/g, '');
      function formatComponentName(vm, includeFile) {
        if (vm.$root === vm) {
          return '<Root>';
        }
        const options = typeof vm === 'function' && vm.cid != null ? vm.options : vm.__isVue ? vm.$options || vm.constructor.options : vm || {};
        let name = options.name || options._componentTag;
        const file = options.__file;
        if (!name && file) {
          const match = file.match(/([^/\\]+)\.vue$/);
          name = match?.[1];
        }
        return (name ? `<${classify(name)}>` : `<Anonymous>`) + (file && includeFile !== false ? ` at ${file}` : '');
      }
      function generateComponentTrace(vm) {
        if (vm.__isVue && vm.$parent) {
          const tree = [];
          let currentRecursiveSequence = 0;
          while (vm) {
            if (tree.length > 0) {
              const last = tree[tree.length - 1];
              if (last.constructor === vm.constructor) {
                currentRecursiveSequence++;
                vm = vm.$parent;
                continue;
              } else if (currentRecursiveSequence > 0) {
                tree[tree.length - 1] = [last, currentRecursiveSequence];
                currentRecursiveSequence = 0;
              }
            }
            tree.push(vm);
            vm = vm.$parent;
          }
          return '\n\nfound in\n\n' + tree.map((vm, i) => `${i === 0 ? '---> ' : ' '.repeat(5 + i * 2)}${Array.isArray(vm)
    // eslint-disable-next-line sonarjs/no-nested-template-literals
    ? `${formatComponentName(vm[0])}... (${vm[1]} recursive calls)` : formatComponentName(vm)}`).join('\n');
        } else {
          return `\n\n(found in ${formatComponentName(vm)})`;
        }
      }

      const srgbForwardMatrix = [[3.2406, -1.5372, -0.4986], [-0.9689, 1.8758, 0.0415], [0.0557, -0.2040, 1.0570]];

      // Forward gamma adjust
      const srgbForwardTransform = C => C <= 0.0031308 ? C * 12.92 : 1.055 * C ** (1 / 2.4) - 0.055;

      // For converting sRGB to XYZ
      const srgbReverseMatrix = [[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]];

      // Reverse gamma adjust
      const srgbReverseTransform = C => C <= 0.04045 ? C / 12.92 : ((C + 0.055) / 1.055) ** 2.4;
      function fromXYZ$1(xyz) {
        const rgb = Array(3);
        const transform = srgbForwardTransform;
        const matrix = srgbForwardMatrix;

        // Matrix transform, then gamma adjustment
        for (let i = 0; i < 3; ++i) {
          // Rescale back to [0, 255]
          rgb[i] = Math.round(clamp(transform(matrix[i][0] * xyz[0] + matrix[i][1] * xyz[1] + matrix[i][2] * xyz[2])) * 255);
        }
        return {
          r: rgb[0],
          g: rgb[1],
          b: rgb[2]
        };
      }
      function toXYZ$1(_ref) {
        let {
          r,
          g,
          b
        } = _ref;
        const xyz = [0, 0, 0];
        const transform = srgbReverseTransform;
        const matrix = srgbReverseMatrix;

        // Rescale from [0, 255] to [0, 1] then adjust sRGB gamma to linear RGB
        r = transform(r / 255);
        g = transform(g / 255);
        b = transform(b / 255);

        // Matrix color space transform
        for (let i = 0; i < 3; ++i) {
          xyz[i] = matrix[i][0] * r + matrix[i][1] * g + matrix[i][2] * b;
        }
        return xyz;
      }

      const delta = 0.20689655172413793; // 6÷29

      const cielabForwardTransform = t => t > delta ** 3 ? Math.cbrt(t) : t / (3 * delta ** 2) + 4 / 29;
      const cielabReverseTransform = t => t > delta ? t ** 3 : 3 * delta ** 2 * (t - 4 / 29);
      function fromXYZ(xyz) {
        const transform = cielabForwardTransform;
        const transformedY = transform(xyz[1]);
        return [116 * transformedY - 16, 500 * (transform(xyz[0] / 0.95047) - transformedY), 200 * (transformedY - transform(xyz[2] / 1.08883))];
      }
      function toXYZ(lab) {
        const transform = cielabReverseTransform;
        const Ln = (lab[0] + 16) / 116;
        return [transform(Ln + lab[1] / 500) * 0.95047, transform(Ln), transform(Ln - lab[2] / 200) * 1.08883];
      }

      // Utilities
      function parseColor(color) {
        if (typeof color === 'number') {
          if (isNaN(color) || color < 0 || color > 0xFFFFFF) {
            // int can't have opacity
            consoleWarn(`'${color}' is not a valid hex color`);
          }
          return {
            r: (color & 0xFF0000) >> 16,
            g: (color & 0xFF00) >> 8,
            b: color & 0xFF
          };
        } else if (typeof color === 'string') {
          let hex = color.startsWith('#') ? color.slice(1) : color;
          if ([3, 4].includes(hex.length)) {
            hex = hex.split('').map(char => char + char).join('');
          } else if (![6, 8].includes(hex.length)) {
            consoleWarn(`'${color}' is not a valid hex(a) color`);
          }
          const int = parseInt(hex, 16);
          if (isNaN(int) || int < 0 || int > 0xFFFFFFFF) {
            consoleWarn(`'${color}' is not a valid hex(a) color`);
          }
          return HexToRGB(hex);
        } else {
          throw new TypeError(`Colors can only be numbers or strings, recieved ${color == null ? color : color.constructor.name} instead`);
        }
      }
      function toHex(v) {
        const h = Math.round(v).toString(16);
        return ('00'.substr(0, 2 - h.length) + h).toUpperCase();
      }
      function RGBtoHex(_ref2) {
        let {
          r,
          g,
          b,
          a
        } = _ref2;
        return `#${[toHex(r), toHex(g), toHex(b), a !== undefined ? toHex(Math.round(a * 255)) : ''].join('')}`;
      }
      function HexToRGB(hex) {
        hex = parseHex(hex);
        let [r, g, b, a] = chunk(hex, 2).map(c => parseInt(c, 16));
        a = a === undefined ? a : a / 255;
        return {
          r,
          g,
          b,
          a
        };
      }
      function parseHex(hex) {
        if (hex.startsWith('#')) {
          hex = hex.slice(1);
        }
        hex = hex.replace(/([^0-9a-f])/gi, 'F');
        if (hex.length === 3 || hex.length === 4) {
          hex = hex.split('').map(x => x + x).join('');
        }
        if (hex.length !== 6) {
          hex = padEnd(padEnd(hex, 6), 8, 'F');
        }
        return hex;
      }
      function lighten(value, amount) {
        const lab = fromXYZ(toXYZ$1(value));
        lab[0] = lab[0] + amount * 10;
        return fromXYZ$1(toXYZ(lab));
      }
      function darken(value, amount) {
        const lab = fromXYZ(toXYZ$1(value));
        lab[0] = lab[0] - amount * 10;
        return fromXYZ$1(toXYZ(lab));
      }

      /**
       * Calculate the relative luminance of a given color
       * @see https://www.w3.org/TR/WCAG20/#relativeluminancedef
       */
      function getLuma(color) {
        const rgb = parseColor(color);
        return toXYZ$1(rgb)[1];
      }

      // Utilities

      const {getCurrentInstance:_getCurrentInstance} = await importShared('vue');
      function getCurrentInstance$1(name, message) {
        const vm = _getCurrentInstance();
        if (!vm) {
          throw new Error(`[Vuetify] ${name} ${message || 'must be called from inside a setup function'}`);
        }
        return vm;
      }
      let _uid = 0;
      let _map = new WeakMap();
      function getUid() {
        const vm = getCurrentInstance$1('getUid');
        if (_map.has(vm)) return _map.get(vm);else {
          const uid = _uid++;
          _map.set(vm, uid);
          return uid;
        }
      }
      getUid.reset = () => {
        _uid = 0;
        _map = new WeakMap();
      };

      function injectSelf(key) {
        const {
          provides
        } = getCurrentInstance$1('injectSelf');
        if (provides && key in provides) {
          // TS doesn't allow symbol as index type
          return provides[key];
        }
      }

      /**
       * Creates a factory function for props definitions.
       * This is used to define props in a composable then override
       * default values in an implementing component.
       *
       * @example Simplified signature
       * (props: Props) => (defaults?: Record<keyof props, any>) => Props
       *
       * @example Usage
       * const makeProps = propsFactory({
       *   foo: String,
       * })
       *
       * defineComponent({
       *   props: {
       *     ...makeProps({
       *       foo: 'a',
       *     }),
       *   },
       *   setup (props) {
       *     // would be "string | undefined", now "string" because a default has been provided
       *     props.foo
       *   },
       * }
       */

      function propsFactory(props, source) {
        return defaults => {
          return Object.keys(props).reduce((obj, prop) => {
            const isObjectDefinition = typeof props[prop] === 'object' && props[prop] != null && !Array.isArray(props[prop]);
            const definition = isObjectDefinition ? props[prop] : {
              type: props[prop]
            };
            if (defaults && prop in defaults) {
              obj[prop] = {
                ...definition,
                default: defaults[prop]
              };
            } else {
              obj[prop] = definition;
            }
            if (source && !obj[prop].source) {
              obj[prop].source = source;
            }
            return obj;
          }, {});
        };
      }

      const {effectScope,onScopeDispose,watch: watch$3} = await importShared('vue');

      function useToggleScope(source, fn) {
        let scope;
        function start() {
          scope = effectScope();
          scope.run(() => fn.length ? fn(() => {
            scope?.stop();
            start();
          }) : fn());
        }
        watch$3(source, active => {
          if (active && !scope) {
            start();
          } else if (!active) {
            scope?.stop();
            scope = undefined;
          }
        }, {
          immediate: true
        });
        onScopeDispose(() => {
          scope?.stop();
        });
      }

      // Utils
      const {defineComponent:_defineComponent,computed: computed$5,getCurrentInstance,shallowRef: shallowRef$1,watchEffect: watchEffect$2} = await importShared('vue');
      function propIsDefined(vnode, prop) {
        return typeof vnode.props?.[prop] !== 'undefined' || typeof vnode.props?.[toKebabCase(prop)] !== 'undefined';
      }

      // No props

      // Implementation
      function defineComponent(options) {
        options._setup = options._setup ?? options.setup;
        if (!options.name) {
          consoleWarn('The component is missing an explicit name, unable to generate default prop value');
          return options;
        }
        if (options._setup) {
          options.props = propsFactory(options.props ?? {}, toKebabCase(options.name))();
          const propKeys = Object.keys(options.props);
          options.filterProps = function filterProps(props) {
            return pick(props, propKeys);
          };
          options.props._as = String;
          options.setup = function setup(props, ctx) {
            const defaults = useDefaults();

            // Skip props proxy if defaults are not provided
            if (!defaults.value) return options._setup(props, ctx);
            const vm = getCurrentInstance();
            const componentDefaults = computed$5(() => defaults.value[props._as ?? options.name]);
            const _props = new Proxy(props, {
              get(target, prop) {
                const propValue = Reflect.get(target, prop);
                if (typeof prop === 'string' && !propIsDefined(vm.vnode, prop)) {
                  return componentDefaults.value?.[prop] ?? defaults.value.global?.[prop] ?? propValue;
                }
                return propValue;
              }
            });
            const _subcomponentDefaults = shallowRef$1();
            watchEffect$2(() => {
              if (componentDefaults.value) {
                const subComponents = Object.entries(componentDefaults.value).filter(_ref => {
                  let [key] = _ref;
                  return key.startsWith(key[0].toUpperCase());
                });
                if (subComponents.length) _subcomponentDefaults.value = Object.fromEntries(subComponents);
              }
            });
            const setupBindings = options._setup(_props, ctx);

            // If subcomponent defaults are provided, override any
            // subcomponents provided by the component's setup function.
            // This uses injectSelf so must be done after the original setup to work.
            useToggleScope(_subcomponentDefaults, () => {
              provideDefaults(mergeDeep(injectSelf(DefaultsSymbol)?.value ?? {}, _subcomponentDefaults.value));
            });
            return setupBindings;
          };
        }
        return options;
      }
      // Implementation
      function genericComponent() {
        let exposeDefaults = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : true;
        return options => (exposeDefaults ? defineComponent : _defineComponent)(options);
      }

      const IN_BROWSER = typeof window !== 'undefined';
      const SUPPORTS_TOUCH = IN_BROWSER && ('ontouchstart' in window || window.navigator.maxTouchPoints > 0);
      IN_BROWSER && typeof CSS !== 'undefined' && typeof CSS.supports !== 'undefined' && CSS.supports('selector(:focus-visible)');

      // Utilities
      const {computed: computed$4,inject: inject$5,provide: provide$3,ref: ref$6,unref} = await importShared('vue');
      const DefaultsSymbol = Symbol.for('vuetify:defaults');
      function createDefaults(options) {
        return ref$6(options);
      }
      function useDefaults() {
        const defaults = inject$5(DefaultsSymbol);
        if (!defaults) throw new Error('[Vuetify] Could not find defaults instance');
        return defaults;
      }
      function provideDefaults(defaults, options) {
        const injectedDefaults = useDefaults();
        const providedDefaults = ref$6(defaults);
        const newDefaults = computed$4(() => {
          const disabled = unref(options?.disabled);
          if (disabled) return injectedDefaults.value;
          const scoped = unref(options?.scoped);
          const reset = unref(options?.reset);
          const root = unref(options?.root);
          let properties = mergeDeep(providedDefaults.value, {
            prev: injectedDefaults.value
          });
          if (scoped) return properties;
          if (reset || root) {
            const len = Number(reset || Infinity);
            for (let i = 0; i <= len; i++) {
              if (!properties || !('prev' in properties)) {
                break;
              }
              properties = properties.prev;
            }
            return properties;
          }
          return properties.prev ? mergeDeep(properties.prev, properties) : properties;
        });
        provide$3(DefaultsSymbol, newDefaults);
        return newDefaults;
      }

      // Utilities
      const {inject: inject$4,reactive: reactive$3,ref: ref$5,shallowRef,toRefs,watchEffect: watchEffect$1} = await importShared('vue');

      const DisplaySymbol = Symbol.for('vuetify:display');
      const defaultDisplayOptions = {
        mobileBreakpoint: 'lg',
        thresholds: {
          xs: 0,
          sm: 600,
          md: 960,
          lg: 1280,
          xl: 1920,
          xxl: 2560
        }
      };
      const parseDisplayOptions = function () {
        let options = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : defaultDisplayOptions;
        return mergeDeep(defaultDisplayOptions, options);
      };
      function getClientWidth(isHydrate) {
        return IN_BROWSER && !isHydrate ? window.innerWidth : 0;
      }
      function getClientHeight(isHydrate) {
        return IN_BROWSER && !isHydrate ? window.innerHeight : 0;
      }
      function getPlatform(isHydrate) {
        const userAgent = IN_BROWSER && !isHydrate ? window.navigator.userAgent : 'ssr';
        function match(regexp) {
          return Boolean(userAgent.match(regexp));
        }
        const android = match(/android/i);
        const ios = match(/iphone|ipad|ipod/i);
        const cordova = match(/cordova/i);
        const electron = match(/electron/i);
        const chrome = match(/chrome/i);
        const edge = match(/edge/i);
        const firefox = match(/firefox/i);
        const opera = match(/opera/i);
        const win = match(/win/i);
        const mac = match(/mac/i);
        const linux = match(/linux/i);
        return {
          android,
          ios,
          cordova,
          electron,
          chrome,
          edge,
          firefox,
          opera,
          win,
          mac,
          linux,
          touch: SUPPORTS_TOUCH,
          ssr: userAgent === 'ssr'
        };
      }
      function createDisplay(options, ssr) {
        const {
          thresholds,
          mobileBreakpoint
        } = parseDisplayOptions(options);
        const height = ref$5(getClientHeight(ssr));
        const platform = shallowRef(getPlatform(ssr));
        const state = reactive$3({});
        const width = ref$5(getClientWidth(ssr));
        function updateSize() {
          height.value = getClientHeight();
          width.value = getClientWidth();
        }
        function update() {
          updateSize();
          platform.value = getPlatform();
        }

        // eslint-disable-next-line max-statements
        watchEffect$1(() => {
          const xs = width.value < thresholds.sm;
          const sm = width.value < thresholds.md && !xs;
          const md = width.value < thresholds.lg && !(sm || xs);
          const lg = width.value < thresholds.xl && !(md || sm || xs);
          const xl = width.value < thresholds.xxl && !(lg || md || sm || xs);
          const xxl = width.value >= thresholds.xxl;
          const name = xs ? 'xs' : sm ? 'sm' : md ? 'md' : lg ? 'lg' : xl ? 'xl' : 'xxl';
          const breakpointValue = typeof mobileBreakpoint === 'number' ? mobileBreakpoint : thresholds[mobileBreakpoint];
          const mobile = width.value < breakpointValue;
          state.xs = xs;
          state.sm = sm;
          state.md = md;
          state.lg = lg;
          state.xl = xl;
          state.xxl = xxl;
          state.smAndUp = !xs;
          state.mdAndUp = !(xs || sm);
          state.lgAndUp = !(xs || sm || md);
          state.xlAndUp = !(xs || sm || md || lg);
          state.smAndDown = !(md || lg || xl || xxl);
          state.mdAndDown = !(lg || xl || xxl);
          state.lgAndDown = !(xl || xxl);
          state.xlAndDown = !xxl;
          state.name = name;
          state.height = height.value;
          state.width = width.value;
          state.mobile = mobile;
          state.mobileBreakpoint = mobileBreakpoint;
          state.platform = platform.value;
          state.thresholds = thresholds;
        });
        if (IN_BROWSER) {
          window.addEventListener('resize', updateSize, {
            passive: true
          });
        }
        return {
          ...toRefs(state),
          update,
          ssr: !!ssr
        };
      }
      function useDisplay() {
        const display = inject$4(DisplaySymbol);
        if (!display) throw new Error('Could not find Vuetify display injection');
        return display;
      }

      // Utilities
      const {h} = await importShared('vue');
      const aliases = {
        collapse: 'mdi-chevron-up',
        complete: 'mdi-check',
        cancel: 'mdi-close-circle',
        close: 'mdi-close',
        delete: 'mdi-close-circle',
        // delete (e.g. v-chip close)
        clear: 'mdi-close-circle',
        success: 'mdi-check-circle',
        info: 'mdi-information',
        warning: 'mdi-alert-circle',
        error: 'mdi-close-circle',
        prev: 'mdi-chevron-left',
        next: 'mdi-chevron-right',
        checkboxOn: 'mdi-checkbox-marked',
        checkboxOff: 'mdi-checkbox-blank-outline',
        checkboxIndeterminate: 'mdi-minus-box',
        delimiter: 'mdi-circle',
        // for carousel
        sortAsc: 'mdi-arrow-up',
        sortDesc: 'mdi-arrow-down',
        expand: 'mdi-chevron-down',
        menu: 'mdi-menu',
        subgroup: 'mdi-menu-down',
        dropdown: 'mdi-menu-down',
        radioOn: 'mdi-radiobox-marked',
        radioOff: 'mdi-radiobox-blank',
        edit: 'mdi-pencil',
        ratingEmpty: 'mdi-star-outline',
        ratingFull: 'mdi-star',
        ratingHalf: 'mdi-star-half-full',
        loading: 'mdi-cached',
        first: 'mdi-page-first',
        last: 'mdi-page-last',
        unfold: 'mdi-unfold-more-horizontal',
        file: 'mdi-paperclip',
        plus: 'mdi-plus',
        minus: 'mdi-minus'
      };
      const mdi = {
        // Not using mergeProps here, functional components merge props by default (?)
        component: props => h(VClassIcon, {
          ...props,
          class: 'mdi'
        })
      };

      const {mergeProps:_mergeProps,createVNode:_createVNode} = await importShared('vue');
      await importShared('vue');
      const IconValue = [String, Function, Object];
      const IconSymbol = Symbol.for('vuetify:icons');
      const makeIconProps = propsFactory({
        icon: {
          type: IconValue
        },
        // Could not remove this and use makeTagProps, types complained because it is not required
        tag: {
          type: String,
          required: true
        }
      }, 'icon');
      genericComponent()({
        name: 'VComponentIcon',
        props: makeIconProps(),
        setup(props, _ref) {
          let {
            slots
          } = _ref;
          return () => {
            return _createVNode(props.tag, null, {
              default: () => [props.icon ? _createVNode(props.icon, null, null) : slots.default?.()]
            });
          };
        }
      });
      const VSvgIcon = defineComponent({
        name: 'VSvgIcon',
        inheritAttrs: false,
        props: makeIconProps(),
        setup(props, _ref2) {
          let {
            attrs
          } = _ref2;
          return () => {
            return _createVNode(props.tag, _mergeProps(attrs, {
              "style": null
            }), {
              default: () => [_createVNode("svg", {
                "class": "v-icon__svg",
                "xmlns": "http://www.w3.org/2000/svg",
                "viewBox": "0 0 24 24",
                "role": "img",
                "aria-hidden": "true"
              }, [_createVNode("path", {
                "d": props.icon
              }, null)])]
            });
          };
        }
      });
      defineComponent({
        name: 'VLigatureIcon',
        props: makeIconProps(),
        setup(props) {
          return () => {
            return _createVNode(props.tag, null, {
              default: () => [props.icon]
            });
          };
        }
      });
      const VClassIcon = defineComponent({
        name: 'VClassIcon',
        props: makeIconProps(),
        setup(props) {
          return () => {
            return _createVNode(props.tag, {
              "class": props.icon
            }, null);
          };
        }
      });
      const defaultSets = {
        svg: {
          component: VSvgIcon
        },
        class: {
          component: VClassIcon
        }
      };

      // Composables
      function createIcons(options) {
        return mergeDeep({
          defaultSet: 'mdi',
          sets: {
            ...defaultSets,
            mdi
          },
          aliases
        }, options);
      }

      // Utilities
      const {computed: computed$3,ref: ref$4,toRaw,watch: watch$2} = await importShared('vue');
      // Composables
      function useProxiedModel(props, prop, defaultValue) {
        let transformIn = arguments.length > 3 && arguments[3] !== undefined ? arguments[3] : v => v;
        let transformOut = arguments.length > 4 && arguments[4] !== undefined ? arguments[4] : v => v;
        const vm = getCurrentInstance$1('useProxiedModel');
        const internal = ref$4(props[prop] !== undefined ? props[prop] : defaultValue);
        const kebabProp = toKebabCase(prop);
        const checkKebab = kebabProp !== prop;
        const isControlled = checkKebab ? computed$3(() => {
          void props[prop];
          return !!((vm.vnode.props?.hasOwnProperty(prop) || vm.vnode.props?.hasOwnProperty(kebabProp)) && (vm.vnode.props?.hasOwnProperty(`onUpdate:${prop}`) || vm.vnode.props?.hasOwnProperty(`onUpdate:${kebabProp}`)));
        }) : computed$3(() => {
          void props[prop];
          return !!(vm.vnode.props?.hasOwnProperty(prop) && vm.vnode.props?.hasOwnProperty(`onUpdate:${prop}`));
        });
        useToggleScope(() => !isControlled.value, () => {
          watch$2(() => props[prop], val => {
            internal.value = val;
          });
        });
        const model = computed$3({
          get() {
            const externalValue = props[prop];
            return transformIn(isControlled.value ? externalValue : internal.value);
          },
          set(internalValue) {
            const newValue = transformOut(internalValue);
            const value = toRaw(isControlled.value ? props[prop] : internal.value);
            if (value === newValue || transformIn(value) === internalValue) {
              return;
            }
            internal.value = newValue;
            vm?.emit(`update:${prop}`, newValue);
          }
        });
        Object.defineProperty(model, 'externalValue', {
          get: () => isControlled.value ? props[prop] : internal.value
        });
        return model;
      }

      const en = {
        badge: 'Badge',
        close: 'Close',
        dataIterator: {
          noResultsText: 'No matching records found',
          loadingText: 'Loading items...'
        },
        dataTable: {
          itemsPerPageText: 'Rows per page:',
          ariaLabel: {
            sortDescending: 'Sorted descending.',
            sortAscending: 'Sorted ascending.',
            sortNone: 'Not sorted.',
            activateNone: 'Activate to remove sorting.',
            activateDescending: 'Activate to sort descending.',
            activateAscending: 'Activate to sort ascending.'
          },
          sortBy: 'Sort by'
        },
        dataFooter: {
          itemsPerPageText: 'Items per page:',
          itemsPerPageAll: 'All',
          nextPage: 'Next page',
          prevPage: 'Previous page',
          firstPage: 'First page',
          lastPage: 'Last page',
          pageText: '{0}-{1} of {2}'
        },
        datePicker: {
          itemsSelected: '{0} selected',
          nextMonthAriaLabel: 'Next month',
          nextYearAriaLabel: 'Next year',
          prevMonthAriaLabel: 'Previous month',
          prevYearAriaLabel: 'Previous year'
        },
        noDataText: 'No data available',
        carousel: {
          prev: 'Previous visual',
          next: 'Next visual',
          ariaLabel: {
            delimiter: 'Carousel slide {0} of {1}'
          }
        },
        calendar: {
          moreEvents: '{0} more'
        },
        input: {
          clear: 'Clear {0}',
          prependAction: '{0} prepended action',
          appendAction: '{0} appended action'
        },
        fileInput: {
          counter: '{0} files',
          counterSize: '{0} files ({1} in total)'
        },
        timePicker: {
          am: 'AM',
          pm: 'PM'
        },
        pagination: {
          ariaLabel: {
            root: 'Pagination Navigation',
            next: 'Next page',
            previous: 'Previous page',
            page: 'Go to page {0}',
            currentPage: 'Page {0}, Current page',
            first: 'First page',
            last: 'Last page'
          }
        },
        rating: {
          ariaLabel: {
            item: 'Rating {0} of {1}'
          }
        },
        loading: 'Loading...'
      };

      const {ref: ref$3,watch: watch$1} = await importShared('vue');
      const LANG_PREFIX = '$vuetify.';
      const replace = (str, params) => {
        return str.replace(/\{(\d+)\}/g, (match, index) => {
          return String(params[+index]);
        });
      };
      const createTranslateFunction = (current, fallback, messages) => {
        return function (key) {
          for (var _len = arguments.length, params = new Array(_len > 1 ? _len - 1 : 0), _key = 1; _key < _len; _key++) {
            params[_key - 1] = arguments[_key];
          }
          if (!key.startsWith(LANG_PREFIX)) {
            return replace(key, params);
          }
          const shortKey = key.replace(LANG_PREFIX, '');
          const currentLocale = current.value && messages.value[current.value];
          const fallbackLocale = fallback.value && messages.value[fallback.value];
          let str = getObjectValueByPath(currentLocale, shortKey, null);
          if (!str) {
            consoleWarn(`Translation key "${key}" not found in "${current.value}", trying fallback locale`);
            str = getObjectValueByPath(fallbackLocale, shortKey, null);
          }
          if (!str) {
            consoleError(`Translation key "${key}" not found in fallback`);
            str = key;
          }
          if (typeof str !== 'string') {
            consoleError(`Translation key "${key}" has a non-string value`);
            str = key;
          }
          return replace(str, params);
        };
      };
      function createNumberFunction(current, fallback) {
        return (value, options) => {
          const numberFormat = new Intl.NumberFormat([current.value, fallback.value], options);
          return numberFormat.format(value);
        };
      }
      function useProvided(props, prop, provided) {
        const internal = useProxiedModel(props, prop, props[prop] ?? provided.value);

        // TODO: Remove when defaultValue works
        internal.value = props[prop] ?? provided.value;
        watch$1(provided, v => {
          if (props[prop] == null) {
            internal.value = provided.value;
          }
        });
        return internal;
      }
      function createProvideFunction(state) {
        return props => {
          const current = useProvided(props, 'locale', state.current);
          const fallback = useProvided(props, 'fallback', state.fallback);
          const messages = useProvided(props, 'messages', state.messages);
          return {
            name: 'vuetify',
            current,
            fallback,
            messages,
            t: createTranslateFunction(current, fallback, messages),
            n: createNumberFunction(current, fallback),
            provide: createProvideFunction({
              current,
              fallback,
              messages
            })
          };
        };
      }
      function createVuetifyAdapter(options) {
        const current = ref$3(options?.locale ?? 'en');
        const fallback = ref$3(options?.fallback ?? 'en');
        const messages = ref$3({
          en,
          ...options?.messages
        });
        return {
          name: 'vuetify',
          current,
          fallback,
          messages,
          t: createTranslateFunction(current, fallback, messages),
          n: createNumberFunction(current, fallback),
          provide: createProvideFunction({
            current,
            fallback,
            messages
          })
        };
      }

      const defaultRtl = {
        af: false,
        ar: true,
        bg: false,
        ca: false,
        ckb: false,
        cs: false,
        de: false,
        el: false,
        en: false,
        es: false,
        et: false,
        fa: true,
        fi: false,
        fr: false,
        hr: false,
        hu: false,
        he: true,
        id: false,
        it: false,
        ja: false,
        ko: false,
        lv: false,
        lt: false,
        nl: false,
        no: false,
        pl: false,
        pt: false,
        ro: false,
        ru: false,
        sk: false,
        sl: false,
        srCyrl: false,
        srLatn: false,
        sv: false,
        th: false,
        tr: false,
        az: false,
        uk: false,
        vi: false,
        zhHans: false,
        zhHant: false
      };

      const {computed: computed$2,inject: inject$3,provide: provide$2,ref: ref$2} = await importShared('vue');
      const LocaleSymbol = Symbol.for('vuetify:locale');
      function isLocaleInstance(obj) {
        return obj.name != null;
      }
      function createLocale(options) {
        const i18n = options?.adapter && isLocaleInstance(options?.adapter) ? options?.adapter : createVuetifyAdapter(options);
        const rtl = createRtl(i18n, options);
        return {
          ...i18n,
          ...rtl
        };
      }
      function useLocale() {
        const locale = inject$3(LocaleSymbol);
        if (!locale) throw new Error('[Vuetify] Could not find injected locale instance');
        return locale;
      }
      function createRtl(i18n, options) {
        const rtl = ref$2(options?.rtl ?? defaultRtl);
        const isRtl = computed$2(() => rtl.value[i18n.current.value] ?? false);
        return {
          isRtl,
          rtl,
          rtlClasses: computed$2(() => `v-locale--is-${isRtl.value ? 'rtl' : 'ltr'}`)
        };
      }
      function useRtl() {
        const locale = inject$3(LocaleSymbol);
        if (!locale) throw new Error('[Vuetify] Could not find injected rtl instance');
        return {
          isRtl: locale.isRtl,
          rtlClasses: locale.rtlClasses
        };
      }

      /**
       * WCAG 3.0 APCA perceptual contrast algorithm from https://github.com/Myndex/SAPC-APCA
       * @licence https://www.w3.org/Consortium/Legal/2015/copyright-software-and-document
       * @see https://www.w3.org/WAI/GL/task-forces/silver/wiki/Visual_Contrast_of_Text_Subgroup
       */

      // MAGICAL NUMBERS

      // sRGB Conversion to Relative Luminance (Y)

      // Transfer Curve (aka "Gamma") for sRGB linearization
      // Simple power curve vs piecewise described in docs
      // Essentially, 2.4 best models actual display
      // characteristics in combination with the total method
      const mainTRC = 2.4;
      const Rco = 0.2126729; // sRGB Red Coefficient (from matrix)
      const Gco = 0.7151522; // sRGB Green Coefficient (from matrix)
      const Bco = 0.0721750; // sRGB Blue Coefficient (from matrix)

      // For Finding Raw SAPC Contrast from Relative Luminance (Y)

      // Constants for SAPC Power Curve Exponents
      // One pair for normal text, and one for reverse
      // These are the "beating heart" of SAPC
      const normBG = 0.55;
      const normTXT = 0.58;
      const revTXT = 0.57;
      const revBG = 0.62;

      // For Clamping and Scaling Values

      const blkThrs = 0.03; // Level that triggers the soft black clamp
      const blkClmp = 1.45; // Exponent for the soft black clamp curve
      const deltaYmin = 0.0005; // Lint trap
      const scaleBoW = 1.25; // Scaling for dark text on light
      const scaleWoB = 1.25; // Scaling for light text on dark
      const loConThresh = 0.078; // Threshold for new simple offset scale
      const loConFactor = 12.82051282051282; // = 1/0.078,
      const loConOffset = 0.06; // The simple offset
      const loClip = 0.001; // Output clip (lint trap #2)

      function APCAcontrast(text, background) {
        // Linearize sRGB
        const Rtxt = (text.r / 255) ** mainTRC;
        const Gtxt = (text.g / 255) ** mainTRC;
        const Btxt = (text.b / 255) ** mainTRC;
        const Rbg = (background.r / 255) ** mainTRC;
        const Gbg = (background.g / 255) ** mainTRC;
        const Bbg = (background.b / 255) ** mainTRC;

        // Apply the standard coefficients and sum to Y
        let Ytxt = Rtxt * Rco + Gtxt * Gco + Btxt * Bco;
        let Ybg = Rbg * Rco + Gbg * Gco + Bbg * Bco;

        // Soft clamp Y when near black.
        // Now clamping all colors to prevent crossover errors
        if (Ytxt <= blkThrs) Ytxt += (blkThrs - Ytxt) ** blkClmp;
        if (Ybg <= blkThrs) Ybg += (blkThrs - Ybg) ** blkClmp;

        // Return 0 Early for extremely low ∆Y (lint trap #1)
        if (Math.abs(Ybg - Ytxt) < deltaYmin) return 0.0;

        // SAPC CONTRAST

        let outputContrast; // For weighted final values
        if (Ybg > Ytxt) {
          // For normal polarity, black text on white
          // Calculate the SAPC contrast value and scale

          const SAPC = (Ybg ** normBG - Ytxt ** normTXT) * scaleBoW;

          // NEW! SAPC SmoothScale™
          // Low Contrast Smooth Scale Rollout to prevent polarity reversal
          // and also a low clip for very low contrasts (lint trap #2)
          // much of this is for very low contrasts, less than 10
          // therefore for most reversing needs, only loConOffset is important
          outputContrast = SAPC < loClip ? 0.0 : SAPC < loConThresh ? SAPC - SAPC * loConFactor * loConOffset : SAPC - loConOffset;
        } else {
          // For reverse polarity, light text on dark
          // WoB should always return negative value.

          const SAPC = (Ybg ** revBG - Ytxt ** revTXT) * scaleWoB;
          outputContrast = SAPC > -loClip ? 0.0 : SAPC > -loConThresh ? SAPC - SAPC * loConFactor * loConOffset : SAPC + loConOffset;
        }
        return outputContrast * 100;
      }

      // Utilities
      const {computed: computed$1,inject: inject$2,provide: provide$1,reactive: reactive$2,ref: ref$1,watch,watchEffect} = await importShared('vue');
      const ThemeSymbol = Symbol.for('vuetify:theme');
      const defaultThemeOptions = {
        defaultTheme: 'light',
        variations: {
          colors: [],
          lighten: 0,
          darken: 0
        },
        themes: {
          light: {
            dark: false,
            colors: {
              background: '#FFFFFF',
              surface: '#FFFFFF',
              'surface-variant': '#424242',
              'on-surface-variant': '#EEEEEE',
              primary: '#6200EE',
              'primary-darken-1': '#3700B3',
              secondary: '#03DAC6',
              'secondary-darken-1': '#018786',
              error: '#B00020',
              info: '#2196F3',
              success: '#4CAF50',
              warning: '#FB8C00'
            },
            variables: {
              'border-color': '#000000',
              'border-opacity': 0.12,
              'high-emphasis-opacity': 0.87,
              'medium-emphasis-opacity': 0.60,
              'disabled-opacity': 0.38,
              'idle-opacity': 0.04,
              'hover-opacity': 0.04,
              'focus-opacity': 0.12,
              'selected-opacity': 0.08,
              'activated-opacity': 0.12,
              'pressed-opacity': 0.12,
              'dragged-opacity': 0.08,
              'theme-kbd': '#212529',
              'theme-on-kbd': '#FFFFFF',
              'theme-code': '#F5F5F5',
              'theme-on-code': '#000000'
            }
          },
          dark: {
            dark: true,
            colors: {
              background: '#121212',
              surface: '#212121',
              'surface-variant': '#BDBDBD',
              'on-surface-variant': '#424242',
              primary: '#BB86FC',
              'primary-darken-1': '#3700B3',
              secondary: '#03DAC5',
              'secondary-darken-1': '#03DAC5',
              error: '#CF6679',
              info: '#2196F3',
              success: '#4CAF50',
              warning: '#FB8C00'
            },
            variables: {
              'border-color': '#FFFFFF',
              'border-opacity': 0.12,
              'high-emphasis-opacity': 0.87,
              'medium-emphasis-opacity': 0.60,
              'disabled-opacity': 0.38,
              'idle-opacity': 0.10,
              'hover-opacity': 0.04,
              'focus-opacity': 0.12,
              'selected-opacity': 0.08,
              'activated-opacity': 0.12,
              'pressed-opacity': 0.16,
              'dragged-opacity': 0.08,
              'theme-kbd': '#212529',
              'theme-on-kbd': '#FFFFFF',
              'theme-code': '#343434',
              'theme-on-code': '#CCCCCC'
            }
          }
        }
      };
      function parseThemeOptions() {
        let options = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : defaultThemeOptions;
        if (!options) return {
          ...defaultThemeOptions,
          isDisabled: true
        };
        const themes = {};
        for (const [key, theme] of Object.entries(options.themes ?? {})) {
          const defaultTheme = theme.dark || key === 'dark' ? defaultThemeOptions.themes?.dark : defaultThemeOptions.themes?.light;
          themes[key] = mergeDeep(defaultTheme, theme);
        }
        return mergeDeep(defaultThemeOptions, {
          ...options,
          themes
        });
      }

      // Composables
      function createTheme(options) {
        const parsedOptions = reactive$2(parseThemeOptions(options));
        const name = ref$1(parsedOptions.defaultTheme);
        const themes = ref$1(parsedOptions.themes);
        const computedThemes = computed$1(() => {
          const acc = {};
          for (const [name, original] of Object.entries(themes.value)) {
            const theme = acc[name] = {
              ...original,
              colors: {
                ...original.colors
              }
            };
            if (parsedOptions.variations) {
              for (const name of parsedOptions.variations.colors) {
                const color = theme.colors[name];
                if (!color) continue;
                for (const variation of ['lighten', 'darken']) {
                  const fn = variation === 'lighten' ? lighten : darken;
                  for (const amount of createRange(parsedOptions.variations[variation], 1)) {
                    theme.colors[`${name}-${variation}-${amount}`] = RGBtoHex(fn(parseColor(color), amount));
                  }
                }
              }
            }
            for (const color of Object.keys(theme.colors)) {
              if (/^on-[a-z]/.test(color) || theme.colors[`on-${color}`]) continue;
              const onColor = `on-${color}`;
              const colorVal = parseColor(theme.colors[color]);
              const blackContrast = Math.abs(APCAcontrast(parseColor(0), colorVal));
              const whiteContrast = Math.abs(APCAcontrast(parseColor(0xffffff), colorVal));

              // TODO: warn about poor color selections
              // const contrastAsText = Math.abs(APCAcontrast(colorVal, colorToInt(theme.colors.background)))
              // const minContrast = Math.max(blackContrast, whiteContrast)
              // if (minContrast < 60) {
              //   consoleInfo(`${key} theme color ${color} has poor contrast (${minContrast.toFixed()}%)`)
              // } else if (contrastAsText < 60 && !['background', 'surface'].includes(color)) {
              //   consoleInfo(`${key} theme color ${color} has poor contrast as text (${contrastAsText.toFixed()}%)`)
              // }

              // Prefer white text if both have an acceptable contrast ratio
              theme.colors[onColor] = whiteContrast > Math.min(blackContrast, 50) ? '#fff' : '#000';
            }
          }
          return acc;
        });
        const current = computed$1(() => computedThemes.value[name.value]);
        const styles = computed$1(() => {
          const lines = [];
          if (current.value.dark) {
            createCssClass(lines, ':root', ['color-scheme: dark']);
          }
          createCssClass(lines, ':root', genCssVariables(current.value));
          for (const [themeName, theme] of Object.entries(computedThemes.value)) {
            createCssClass(lines, `.v-theme--${themeName}`, [`color-scheme: ${theme.dark ? 'dark' : 'normal'}`, ...genCssVariables(theme)]);
          }
          const bgLines = [];
          const fgLines = [];
          const colors = new Set(Object.values(computedThemes.value).flatMap(theme => Object.keys(theme.colors)));
          for (const key of colors) {
            if (/^on-[a-z]/.test(key)) {
              createCssClass(fgLines, `.${key}`, [`color: rgb(var(--v-theme-${key})) !important`]);
            } else {
              createCssClass(bgLines, `.bg-${key}`, [`--v-theme-overlay-multiplier: var(--v-theme-${key}-overlay-multiplier)`, `background-color: rgb(var(--v-theme-${key})) !important`, `color: rgb(var(--v-theme-on-${key})) !important`]);
              createCssClass(fgLines, `.text-${key}`, [`color: rgb(var(--v-theme-${key})) !important`]);
              createCssClass(fgLines, `.border-${key}`, [`--v-border-color: var(--v-theme-${key})`]);
            }
          }
          lines.push(...bgLines, ...fgLines);
          return lines.map((str, i) => i === 0 ? str : `    ${str}`).join('');
        });
        function getHead() {
          return {
            style: [{
              children: styles.value,
              id: 'vuetify-theme-stylesheet',
              nonce: parsedOptions.cspNonce || false
            }]
          };
        }
        function install(app) {
          const head = app._context.provides.usehead;
          if (head) {
            if (head.push) {
              const entry = head.push(getHead);
              watch(styles, () => {
                entry.patch(getHead);
              });
            } else {
              if (IN_BROWSER) {
                head.addHeadObjs(computed$1(getHead));
                watchEffect(() => head.updateDOM());
              } else {
                head.addHeadObjs(getHead());
              }
            }
          } else {
            let styleEl = IN_BROWSER ? document.getElementById('vuetify-theme-stylesheet') : null;
            watch(styles, updateStyles, {
              immediate: true
            });
            function updateStyles() {
              if (parsedOptions.isDisabled) return;
              if (typeof document !== 'undefined' && !styleEl) {
                const el = document.createElement('style');
                el.type = 'text/css';
                el.id = 'vuetify-theme-stylesheet';
                if (parsedOptions.cspNonce) el.setAttribute('nonce', parsedOptions.cspNonce);
                styleEl = el;
                document.head.appendChild(styleEl);
              }
              if (styleEl) styleEl.innerHTML = styles.value;
            }
          }
        }
        const themeClasses = computed$1(() => parsedOptions.isDisabled ? undefined : `v-theme--${name.value}`);
        return {
          install,
          isDisabled: parsedOptions.isDisabled,
          name,
          themes,
          current,
          computedThemes,
          themeClasses,
          styles,
          global: {
            name,
            current
          }
        };
      }
      function useTheme() {
        getCurrentInstance$1('useTheme');
        const theme = inject$2(ThemeSymbol, null);
        if (!theme) throw new Error('Could not find Vuetify theme injection');
        return theme;
      }
      function createCssClass(lines, selector, content) {
        lines.push(`${selector} {\n`, ...content.map(line => `  ${line};\n`), '}\n');
      }
      function genCssVariables(theme) {
        const lightOverlay = theme.dark ? 2 : 1;
        const darkOverlay = theme.dark ? 1 : 2;
        const variables = [];
        for (const [key, value] of Object.entries(theme.colors)) {
          const rgb = parseColor(value);
          variables.push(`--v-theme-${key}: ${rgb.r},${rgb.g},${rgb.b}`);
          if (!key.startsWith('on-')) {
            variables.push(`--v-theme-${key}-overlay-multiplier: ${getLuma(value) > 0.18 ? lightOverlay : darkOverlay}`);
          }
        }
        for (const [key, value] of Object.entries(theme.variables)) {
          const color = typeof value === 'string' && value.startsWith('#') ? parseColor(value) : undefined;
          const rgb = color ? `${color.r}, ${color.g}, ${color.b}` : undefined;
          variables.push(`--v-${key}: ${rgb ?? value}`);
        }
        return variables;
      }

      const {computed,inject: inject$1,onActivated,onBeforeUnmount,onDeactivated,onMounted,provide,reactive: reactive$1,ref} = await importShared('vue');
      const VuetifyLayoutKey = Symbol.for('vuetify:layout');
      function useLayout() {
        const layout = inject$1(VuetifyLayoutKey);
        if (!layout) throw new Error('[Vuetify] Could not find injected layout');
        return {
          getLayoutItem: layout.getLayoutItem,
          mainRect: layout.mainRect,
          mainStyles: layout.mainStyles
        };
      }

      const {nextTick,reactive} = await importShared('vue');
      function createVuetify() {
        let vuetify = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : {};
        const {
          blueprint,
          ...rest
        } = vuetify;
        const options = mergeDeep(blueprint, rest);
        const {
          aliases = {},
          components = {},
          directives = {}
        } = options;
        const defaults = createDefaults(options.defaults);
        const display = createDisplay(options.display, options.ssr);
        const theme = createTheme(options.theme);
        const icons = createIcons(options.icons);
        const locale = createLocale(options.locale);
        const install = app => {
          for (const key in directives) {
            app.directive(key, directives[key]);
          }
          for (const key in components) {
            app.component(key, components[key]);
          }
          for (const key in aliases) {
            app.component(key, defineComponent({
              ...aliases[key],
              name: key,
              aliasName: aliases[key].name
            }));
          }
          theme.install(app);
          app.provide(DefaultsSymbol, defaults);
          app.provide(DisplaySymbol, display);
          app.provide(ThemeSymbol, theme);
          app.provide(IconSymbol, icons);
          app.provide(LocaleSymbol, locale);
          if (IN_BROWSER && options.ssr) {
            if (app.$nuxt) {
              app.$nuxt.hook('app:suspense:resolve', () => {
                display.update();
              });
            } else {
              const {
                mount
              } = app;
              app.mount = function () {
                const vm = mount(...arguments);
                nextTick(() => display.update());
                app.mount = mount;
                return vm;
              };
            }
          }
          getUid.reset();
          {
            app.mixin({
              computed: {
                $vuetify() {
                  return reactive({
                    defaults: inject.call(this, DefaultsSymbol),
                    display: inject.call(this, DisplaySymbol),
                    theme: inject.call(this, ThemeSymbol),
                    icons: inject.call(this, IconSymbol),
                    locale: inject.call(this, LocaleSymbol)
                  });
                }
              }
            });
          }
        };
        return {
          install,
          defaults,
          display,
          theme,
          icons,
          locale
        };
      }
      const version = exports('version', "3.1.14");
      createVuetify.version = version;

      // Vue's inject() can only be used in setup
      function inject(key) {
        const vm = this.$;
        const provides = vm.parent?.provides ?? vm.vnode.appContext?.provides;
        if (provides && key in provides) {
          return provides[key];
        }
      }

    })
  };
}));
