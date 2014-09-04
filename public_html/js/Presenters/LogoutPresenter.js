var App = App || {};
App.Presenters = App.Presenters || {};

App.Presenters.LogoutPresenter = function(
	jQuery,
	topNavigationPresenter,
	messagePresenter,
	auth,
	promise,
	router) {

	var $messages = jQuery('#content');

	function init() {
		topNavigationPresenter.select('logout');
		promise.wait(auth.logout()).then(function() {
			$messages.empty();
			var $messageDiv = messagePresenter.showInfo($messages, 'Logged out. <a href="">Back to main page</a>');
			$messageDiv.find('a').click(mainPageLinkClicked);
		}).fail(function(response) {
			messagePresenter.showError($messages, response.json && response.json.error || response);
		});
	}

	function mainPageLinkClicked(e) {
		e.preventDefault();
		router.navigateToMainPage();
	}

	return {
		init: init
	};

};

App.DI.register('logoutPresenter', App.Presenters.LogoutPresenter);
