/**
 * portfolio-render.js
 * Shared engine used by every portfolioN.html template.
 * Reads the parsed resume JSON (produced by the Flask backend) out of
 * sessionStorage and fills in the template using three simple HTML
 * attributes — no per-template JS required.
 *
 *   data-field="name"              -> element.textContent = data.name
 *   data-field="links.github"      -> supports dot paths for nested objects
 *   data-link="links.github"       -> element.href = data.links.github (hides el if empty)
 *   data-repeat-chips="skills"     -> repeats the container's first child once per array item (flat string arrays)
 *   data-repeat="experience"       -> marks a template node; cloned once per item in data.experience,
 *                                      each clone's inner [data-field] / [data-repeat-chips] get filled
 *                                      from that single item (e.g. item.tech for projects)
 */
(function () {
  function getData() {
    const raw = sessionStorage.getItem('resumeData');
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch (e) {
      console.error('resumeData in sessionStorage is not valid JSON', e);
      return null;
    }
  }

  function getPath(obj, path) {
    return path.split('.').reduce((o, k) => (o == null ? undefined : o[k]), obj);
  }

  function bindSimpleFields(root, data) {
    root.querySelectorAll('[data-field]').forEach((el) => {
      const val = getPath(data, el.getAttribute('data-field'));
      if (val !== undefined && val !== null && val !== '') el.textContent = val;
    });
  }

  function resolveHref(key, val) {
    if (/^https?:\/\/|^mailto:|^tel:/i.test(val)) return val;
    if (key === 'email') return 'mailto:' + val;
    if (key === 'phone') return 'tel:' + val;
    return 'https://' + val;
  }

  function bindLinks(root, data) {
    root.querySelectorAll('[data-link]').forEach((el) => {
      const key = el.getAttribute('data-link');
      const val = getPath(data, key);
      if (val) {
        el.href = resolveHref(key, val);
      } else {
        el.style.display = 'none';
      }
    });
  }

  function fillChips(container, list) {
    if (!Array.isArray(list) || !list.length) {
      container.style.display = 'none';
      return;
    }
    const template = container.firstElementChild;
    if (!template) return;
    container.innerHTML = '';
    list.forEach((val) => {
      const chip = template.cloneNode(true);
      chip.textContent = val;
      container.appendChild(chip);
    });
  }

  function bindChipContainers(root, data) {
    // only handles containers that are NOT inside a data-repeat template
    root.querySelectorAll('[data-repeat-chips]').forEach((container) => {
      if (container.closest('[data-repeat]')) return; // handled per-item instead
      fillChips(container, getPath(data, container.getAttribute('data-repeat-chips')));
    });
  }

  function bindRepeats(root, data) {
    root.querySelectorAll('[data-repeat]').forEach((templateEl) => {
      const key = templateEl.getAttribute('data-repeat');
      const list = getPath(data, key);
      const parent = templateEl.parentElement;

      if (!Array.isArray(list) || !list.length) {
        templateEl.remove();
        return;
      }

      const blank = templateEl.cloneNode(true);
      blank.removeAttribute('data-repeat');

      list.forEach((item) => {
        const node = blank.cloneNode(true);
        node.querySelectorAll('[data-field]').forEach((fieldEl) => {
          const fkey = fieldEl.getAttribute('data-field');
          const val = fkey === '.' ? item : getPath(item, fkey);
          if (val !== undefined && val !== null && val !== '') fieldEl.textContent = val;
        });
        node.querySelectorAll('[data-link]').forEach((linkEl) => {
          const lkey = linkEl.getAttribute('data-link');
          const val = getPath(item, lkey);
          if (val) linkEl.href = resolveHref(lkey, val);
          else linkEl.style.display = 'none';
        });
        node.querySelectorAll('[data-repeat-chips]').forEach((chipContainer) => {
          fillChips(chipContainer, getPath(item, chipContainer.getAttribute('data-repeat-chips')));
        });
        parent.insertBefore(node, templateEl);
      });

      templateEl.remove();
    });
  }

  function init() {
    const data = getData();
    if (!data) {
      console.warn('No resume data found in sessionStorage — showing template placeholder content.');
      return;
    }
    bindSimpleFields(document, data);
    bindLinks(document, data);
    bindRepeats(document, data); // must run before flat chip binding so it can skip nested ones
    bindChipContainers(document, data);
    if (data.name) document.title = data.name + (data.title ? ' — ' + data.title : '');
  }

  document.addEventListener('DOMContentLoaded', init);

  // Exposed so each template's "Download" button can call downloadPortfolio()
  window.downloadPortfolio = function (filename) {
    const html = '<!DOCTYPE html>\n' + document.documentElement.outerHTML;
    const blob = new Blob([html], { type: 'text/html' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = (filename || 'portfolio') + '.html';
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(a.href);
  };
})();