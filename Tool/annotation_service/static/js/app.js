var app = angular.module("annotate",[]);

app.controller("TutorialController",function($scope,$http,$location) {
    $scope.section1_show = true;
    $scope.show_context = false;
    $scope.toggleContext = function() {
        $scope.show_context = !$scope.show_context   ;
    };
});

app.controller("WF1aController",function($scope,$http,$location) {
    $scope.section1_show = true;
    $scope.show_context = false;
    $scope.toggleContext = function() {
        $scope.show_context = !$scope.show_context   ;
    };
});


app.controller("WF1bController",function($scope,$http,$location) {
    $scope.section1_show = true;
    $scope.show_context = false;
    $scope.toggleContext = function() {
        $scope.show_context = !$scope.show_context   ;
    };
});