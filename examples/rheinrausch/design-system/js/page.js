/* RheinRausch page behaviour: filter chips, experience detail dialog, demo booking.
   No dependencies. Reads everything from the markup, so a template can output the cards and nothing else is needed.

   Markup contract:
   - Filter chips:  <button data-filter="Abends" aria-pressed="false">   ("Alle" shows all)
   - Cards:         <button class="rr-card rr-line--rides" data-title data-text data-duration data-price data-status
                    data-status-tone="gruen|pink|navy">
                    The line class (rr-line--rides, river, nights, kolsch, quest, business) fixes colour and icon in the CSS.
   - Empty message: <p id="empty" hidden>
   - Dialog:        <div class="rr-modal" id="modal" hidden data-done="Gebucht! ..." data-name-fallback="du"> with the
                    ids m-icon (a <span class="rr-card__icon">), m-status, m-title, m-text, m-dur, m-price, m-close, m-book,
                    m-name, m-go, m-done, m-done-text. The script gives m-icon the line class of the card that was opened.
   Filter: each line has fixed tags (LINE_TAGS below). A chip shows the cards whose line has its label as a tag.
   Change the chip labels and LINE_TAGS together. */
(function () {
  var tone = { gruen: 'rr-badge--gruen', pink: '', navy: 'rr-badge--navy' };
  var LINE_TAGS = {
    rides: ['Draußen', 'Gruppen'], river: ['Draußen'], nights: ['Abends', 'Gruppen'],
    kolsch: ['Abends', 'Gruppen'], quest: ['Draußen', 'Team'], business: ['Team', 'Gruppen']
  };
  var lineOf = function (card) { var m = /rr-line--(\w+)/.exec(card.className); return m ? m[1] : ''; };
  var cards = [].slice.call(document.querySelectorAll('.rr-card'));
  var chips = [].slice.call(document.querySelectorAll('[data-filter]'));
  var modal = document.getElementById('modal');
  var last = null;
  var $ = function (id) { return document.getElementById(id); };

  chips.forEach(function (chip) {
    chip.addEventListener('click', function () {
      var tag = chip.getAttribute('data-filter'), shown = 0;
      chips.forEach(function (c) { c.setAttribute('aria-pressed', c === chip ? 'true' : 'false'); });
      cards.forEach(function (card) {
        var ok = tag === 'Alle' || (LINE_TAGS[lineOf(card)] || []).indexOf(tag) > -1;
        card.hidden = !ok; if (ok) shown++;
      });
      if ($('empty')) $('empty').hidden = shown > 0;
    });
  });

  if (!modal) return;

  function open(card) {
    last = card;
    $('m-icon').className = 'rr-card__icon rr-line--' + lineOf(card);
    var st = $('m-status');
    st.textContent = card.getAttribute('data-status') || '';
    st.className = 'rr-badge rr-badge--ink ' + (tone[card.getAttribute('data-status-tone')] || '');
    $('m-title').textContent = card.getAttribute('data-title') || '';
    $('m-text').textContent = card.getAttribute('data-text') || '';
    $('m-dur').textContent = card.getAttribute('data-duration') || '';
    $('m-price').textContent = card.getAttribute('data-price') || '';
    $('m-book').hidden = false; $('m-done').hidden = true;
    modal.hidden = false; $('m-close').focus();
  }
  function close() { modal.hidden = true; if (last) last.focus(); }

  cards.forEach(function (card) { card.addEventListener('click', function () { open(card); }); });
  $('m-close').addEventListener('click', close);
  modal.addEventListener('click', function (ev) { if (ev.target === modal) close(); });
  document.addEventListener('keydown', function (ev) { if (ev.key === 'Escape' && !modal.hidden) close(); });
  $('m-go').addEventListener('click', function () {
    var n = ($('m-name').value || '').trim() || modal.getAttribute('data-name-fallback') || '';
    $('m-done-text').textContent = (modal.getAttribute('data-done') || '') + ' ' + n + '.';
    $('m-book').hidden = true; $('m-done').hidden = false;
  });
})();
