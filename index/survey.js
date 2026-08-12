const EVENTS = [
  { id: 'calc', name: 'Calculator Applications', path: 'events/calcapps/calc.html', grades: [6,7,8], desc: 'Applied math with a calculator against the clock.' },
  { id: 'chess', name: 'Chess Puzzle', path: 'events/chess/chess.html', grades: [2,3,4,5,6,7,8], desc: 'Tactical pattern recognition and strategic thinking.' },
  { id: 'imprompt', name: 'Impromptu Speaking', path: 'events/impromptu/imprompt.html', grades: [6,7,8], desc: 'A structured speech on an unseen topic with minimal preparation.' },
  { id: 'math', name: 'Mathematics', path: 'events/mathematics/math.html', grades: [6,7,8], desc: 'Broad middle-school mathematics without a calculator.' },
  { id: 'oratory', name: 'Modern Oratory', path: 'events/OO/oratory.html', grades: [6,7,8], desc: 'A researched, memorized persuasive speech on a public issue.' },
  { id: 'numsense', name: 'Number Sense', path: 'events/numbersense/numsense.html', grades: [4,5,6,7,8], desc: 'Fast mental arithmetic without scratch work.' },
  { id: 'oral', name: 'Oral Reading', path: 'events/oralreading/oral.html', grades: [4,5,6,7,8,9], desc: 'Literary interpretation through live oral delivery.' },
  { id: 'science', name: 'Science', path: 'events/science/science.html', grades: [6,7,8], desc: 'Cross-grade TEKS, scientific reasoning, and wildcard topics.' },
  { id: 'social', name: 'Social Studies', path: 'events/socialStudies/social.html', grades: [5,6,7,8], desc: 'History, geography, government, economics, and primary sources.' },
  { id: 'spelling', name: 'Spelling', path: 'events/spelling/spelling.html', grades: [3,4,5,6,7,8], desc: 'Dictated spelling, capitalization, punctuation, and word knowledge.' }
];

const QUESTIONS = [
  { id: 'grade', short: 'Your grade', label: 'About you', text: 'What grade are you currently in?', hint: 'We’ll only recommend events that include your grade.', type: 'single', options: [2,3,4,5,6,7,8,9].map((grade) => ({ value: String(grade), label: `Grade ${grade}` })) },
  { id: 'domain', short: 'Academic domain', label: 'Question 1 of 6', text: 'Which academic domain feels strongest to you?', hint: 'Choose the answer that feels most natural—not the one you think you should pick.', type: 'single', options: [
    { value:'math', label:'Mathematics & numbers', sub:'Arithmetic, algebra, and computation' }, { value:'words', label:'Language & writing', sub:'Reading, vocabulary, and composition' }, { value:'science', label:'Science & how things work', sub:'Biology, chemistry, physics, and earth science' }, { value:'speaking', label:'Communication & rhetoric', sub:'Speaking, persuasion, and storytelling' }, { value:'history', label:'History & social studies', sub:'Events, geography, government, and economics' }, { value:'strategy', label:'Logic & strategic thinking', sub:'Puzzles, patterns, and planning ahead' }
  ]},
  { id: 'pace', short: 'Working pace', label: 'Question 2 of 6', text: 'How do you naturally work through a difficult problem?', hint: 'Think about the approach you use under time pressure.', type: 'single', options: [
    { value:'fast', label:'Quickly and instinctively', sub:'Pattern recognition and speed' }, { value:'steady', label:'Methodically and precisely', sub:'Careful, step-by-step work' }, { value:'creative', label:'Creatively and flexibly', sub:'New angles and novel approaches' }
  ]},
  { id: 'audience', short: 'Stage comfort', label: 'Question 3 of 6', text: 'How comfortable are you speaking or performing for an audience?', hint: 'There are strong UIL options both on stage and off.', type: 'single', options: [
    { value:'yes', label:'Very comfortable', sub:'An audience adds energy' }, { value:'neutral', label:'Somewhat comfortable', sub:'I can do it, but it is not my first choice' }, { value:'no', label:'Not my preference', sub:'I work best alone or in writing' }
  ]},
  { id: 'prep', short: 'Preparation style', label: 'Question 4 of 6', text: 'What kind of preparation works best for you?', hint: 'Choose the routine you would be most likely to maintain.', type: 'single', options: [
    { value:'memorize', label:'Systematic memorization', sub:'Flashcards, repetition, and review' }, { value:'drill', label:'Timed drills and practice', sub:'Reps under realistic pressure' }, { value:'write', label:'Research and rehearsal', sub:'Read, draft, refine, and present' }, { value:'think', label:'Problem sets and reasoning', sub:'Build models and solve novel problems' }
  ]},
  { id: 'enjoy', short: 'Favorite subjects', label: 'Question 5 of 6', text: 'Which subjects do you genuinely enjoy?', hint: 'Select as many as you like—or continue without choosing one.', type: 'multi', options: [
    { value:'math', label:'Mathematics' }, { value:'english', label:'English / Language Arts' }, { value:'science', label:'Science' }, { value:'ss', label:'Social Studies' }, { value:'speech', label:'Speech, Theatre, or Debate' }, { value:'cs', label:'Computer Science / Technology' }
  ]},
  { id: 'compete', short: 'Competition format', label: 'Question 6 of 6', text: 'Which competition format suits you best?', hint: 'Imagine the environment where you would feel most focused.', type: 'single', options: [
    { value:'test', label:'Written test', sub:'Solo work in a quiet room' }, { value:'stage', label:'Live delivery', sub:'Performance in front of judges' }, { value:'timed', label:'Race against the clock', sub:'Speed and accuracy under pressure' }, { value:'puzzle', label:'Analytical challenge', sub:'Reasoning and pattern recognition' }
  ]}
];

const answers = {};
let current = 0;
let showingResults = false;

const content = document.getElementById('assessment-content');
const actions = document.getElementById('assessment-actions');
const backButton = document.getElementById('back-button');
const nextButton = document.getElementById('next-button');
const progressFill = document.getElementById('progress-fill');
const stepList = document.getElementById('step-list');

stepList.innerHTML = QUESTIONS.map((question, index) => `<li data-step="${index}"><span class="step-dot">${index + 1}</span><span>${question.short}</span></li>`).join('');

function updateProgress() {
  const steps = [...stepList.children];
  steps.forEach((step, index) => {
    step.classList.toggle('active', !showingResults && index === current);
    step.classList.toggle('done', showingResults || index < current);
    step.querySelector('.step-dot').textContent = (showingResults || index < current) ? '✓' : String(index + 1);
  });
  progressFill.style.width = showingResults ? '100%' : `${(current / QUESTIONS.length) * 100}%`;
}

function renderQuestion() {
  showingResults = false;
  const question = QUESTIONS[current];
  const selected = answers[question.id];
  const selectedValues = Array.isArray(selected) ? selected : [selected];
  const gradeClass = question.id === 'grade' ? ' grade-grid' : '';

  content.innerHTML = `
    <div class="assessment-status"><span>${question.label}</span><span>${current + 1} / ${QUESTIONS.length}</span></div>
    <div class="question">
      <h2 id="question-title">${question.text}</h2>
      <p class="question-hint" id="question-hint">${question.hint}</p>
      <div class="option-grid${gradeClass}" role="group" aria-labelledby="question-title" aria-describedby="question-hint">
        ${question.options.map((option) => `<button class="option" type="button" data-value="${option.value}" aria-pressed="${selectedValues.includes(option.value)}"><strong>${option.label}</strong>${option.sub ? `<span>${option.sub}</span>` : ''}</button>`).join('')}
      </div>
    </div>`;

  content.querySelectorAll('.option').forEach((button) => button.addEventListener('click', () => selectOption(question, button)));
  backButton.disabled = current === 0;
  nextButton.disabled = question.type !== 'multi' && !answers[question.id];
  nextButton.textContent = current === QUESTIONS.length - 1 ? 'See results →' : 'Continue →';
  actions.hidden = false;
  updateProgress();
}

function selectOption(question, button) {
  const value = button.dataset.value;
  if (question.type === 'multi') {
    const selected = new Set(answers[question.id] || []);
    selected.has(value) ? selected.delete(value) : selected.add(value);
    answers[question.id] = [...selected];
    button.setAttribute('aria-pressed', String(selected.has(value)));
  } else {
    answers[question.id] = value;
    content.querySelectorAll('.option').forEach((option) => option.setAttribute('aria-pressed', String(option === button)));
  }
  nextButton.disabled = false;
}

function calculateScores() {
  const grade = Number(answers.grade || 6);
  const domainMap = { math:['calc','math','numsense','chess'], words:['spelling','oral','oratory','imprompt'], science:['science'], speaking:['imprompt','oratory','oral'], history:['social'], strategy:['chess','math','numsense'] };
  const paceMap = { fast:['calc','numsense'], steady:['math','science','social','spelling','chess'], creative:['imprompt','oratory','oral'] };
  const prepMap = { memorize:['spelling','social','science','chess'], drill:['calc','numsense','math'], write:['oratory','imprompt'], think:['math','chess','imprompt'] };
  const classMap = { math:['calc','math','numsense'], english:['spelling','oral','imprompt','oratory'], science:['science'], ss:['social'], speech:['imprompt','oratory','oral'], cs:['calc','numsense','chess'] };
  const formatMap = { test:['math','science','social','spelling'], stage:['imprompt','oratory','oral'], timed:['calc','numsense'], puzzle:['chess','math'] };
  const speechEvents = ['imprompt','oratory','oral'];

  return EVENTS.filter((event) => event.grades.includes(grade)).map((event) => {
    let points = 8;
    const reasons = [];
    if (domainMap[answers.domain]?.includes(event.id)) { points += 30; reasons.push('fits your strongest domain'); }
    if (paceMap[answers.pace]?.includes(event.id)) { points += 14; reasons.push('matches your natural pace'); }
    if (answers.audience === 'yes' && speechEvents.includes(event.id)) { points += 20; reasons.push('uses your stage confidence'); }
    if (answers.audience === 'no' && speechEvents.includes(event.id)) points -= 22;
    if (answers.audience === 'no' && !speechEvents.includes(event.id)) { points += 6; reasons.push('does not require live delivery'); }
    if (answers.audience === 'neutral' && speechEvents.includes(event.id)) points += 6;
    if (prepMap[answers.prep]?.includes(event.id)) { points += 12; reasons.push('fits how you prepare'); }
    for (const subject of (answers.enjoy || [])) {
      if (classMap[subject]?.includes(event.id)) { points += 10; reasons.push('connects with a subject you enjoy'); break; }
    }
    if (formatMap[answers.compete]?.includes(event.id)) { points += 18; reasons.push('matches your preferred format'); }
    return { ...event, points: Math.max(0, points), reasons: [...new Set(reasons)].slice(0, 2) };
  }).filter((event) => event.points > 0).sort((a, b) => b.points - a.points);
}

function renderResults() {
  showingResults = true;
  const scored = calculateScores();
  const top = scored.slice(0, 5);
  const max = top[0]?.points || 1;
  content.innerHTML = `
    <div class="assessment-status"><span>Assessment complete</span><span>Personalized results</span></div>
    <div class="results">
      <span class="eyebrow">Your recommended events</span>
      <h2>Start with these conversations.</h2>
      <p class="results-intro">These eligible events align most closely with your answers. Bring the list to your coach to confirm availability and fit.</p>
      <div class="result-list">
        ${top.map((event, index) => { const match = Math.round((event.points / max) * 100); return `<article class="result-row" style="animation-delay:${index * 65}ms"><span class="result-rank">${index + 1}</span><div><a class="result-name" href="${event.path}">${event.name} →</a><span class="result-why">${event.reasons.length ? event.reasons.join(' · ') : event.desc}</span></div><span class="result-score">${match}% match</span></article>`; }).join('')}
      </div>
      <div class="button-row"><a class="button" href="event.html">Compare event details</a><button class="button button-outline" type="button" id="retake-button">Retake assessment</button></div>
    </div>`;
  actions.hidden = true;
  updateProgress();
  document.getElementById('retake-button').addEventListener('click', retake);
  content.focus({ preventScroll: true });
}

function retake() {
  Object.keys(answers).forEach((key) => delete answers[key]);
  current = 0;
  renderQuestion();
  content.focus({ preventScroll: true });
}

backButton.addEventListener('click', () => {
  if (current > 0) { current -= 1; renderQuestion(); content.focus({ preventScroll: true }); }
});

nextButton.addEventListener('click', () => {
  if (current === QUESTIONS.length - 1) renderResults();
  else { current += 1; renderQuestion(); content.focus({ preventScroll: true }); }
});

renderQuestion();
